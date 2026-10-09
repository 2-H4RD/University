from dataclasses import dataclass
from typing import Dict, List, Tuple
from collections import Counter
import re
import xml.etree.ElementTree as ET

import numpy as np

_XML_DECL_RE = re.compile(r'^\s*<\?xml[^>]*\?>', re.IGNORECASE)
_BARE_AMP_RE = re.compile(r'&(?!#\d+;|#x[0-9A-Fa-f]+;|[A-Za-z][A-Za-z0-9]+;)')


@dataclass(frozen=True)
class SentencePair:
    """Contains lists of tokens for source and target sentence."""
    source: List[str]
    target: List[str]


@dataclass(frozen=True)
class TokenizedSentencePair:
    """Contains arrays of token vocabulary indices."""
    source_tokens: np.ndarray
    target_tokens: np.ndarray


@dataclass(frozen=True)
class LabeledAlignment:
    """Positions are numbered from 1. First coordinate is source position."""
    sure: List[Tuple[int, int]]
    possible: List[Tuple[int, int]]


def _text_of_first(elem, names):
    names = {name.lower() for name in names}
    for child in list(elem):
        tag = child.tag.split('}')[-1].lower()
        if tag in names:
            return (child.text or '').strip()
    return ''


def _parse_alignment(text: str) -> List[Tuple[int, int]]:
    pairs = []
    if not text:
        return pairs
    for a, b in re.findall(r'(\d+)\s*[-:,]\s*(\d+)', text):
        pairs.append((int(a), int(b)))
    if not pairs:
        nums = [int(x) for x in re.findall(r'\d+', text)]
        pairs = list(zip(nums[::2], nums[1::2]))
    return pairs


def _prepare_xml(content: str, wrap: bool = False) -> str:
    """Make CzEnAli XML-like files parseable by ElementTree."""
    content = _BARE_AMP_RE.sub('&amp;', content)
    if wrap:
        content = _XML_DECL_RE.sub('', content, count=1).lstrip()
        return '<root>\n' + content + '\n</root>'
    return content


def extract_sentences(filename: str) -> Tuple[List[SentencePair], List[LabeledAlignment]]:
    """Parse CzEnAli-style XML/WA file."""
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    try:
        root = ET.fromstring(_prepare_xml(content))
    except ET.ParseError:
        root = ET.fromstring(_prepare_xml(content, wrap=True))

    sentence_pairs = []
    alignments = []
    nodes = [root] if root.tag.split('}')[-1].lower() in {'s', 'sentence'} else list(root.iter())

    for node in nodes:
        tag = node.tag.split('}')[-1].lower()
        if tag not in {'s', 'sentence'}:
            continue

        src = _text_of_first(node, ['english', 'source', 'src', 'en'])
        tgt = _text_of_first(node, ['czech', 'target', 'tgt', 'cz', 'cs'])
        sure = _text_of_first(node, ['sure', 'certain'])
        possible = _text_of_first(node, ['possible', 'probable'])

        if not src or not tgt:
            continue

        src_tokens = src.split()
        tgt_tokens = tgt.split()
        sure_pairs = _parse_alignment(sure)
        possible_pairs = _parse_alignment(possible)
        possible_set = set(possible_pairs) | set(sure_pairs)

        sentence_pairs.append(SentencePair(src_tokens, tgt_tokens))
        alignments.append(LabeledAlignment(sorted(set(sure_pairs)), sorted(possible_set)))

    return sentence_pairs, alignments


def get_token_to_index(sentence_pairs: List[SentencePair], freq_cutoff=None) -> Tuple[Dict[str, int], Dict[str, int]]:
    """Create source and target token->index dictionaries."""
    src_counter = Counter()
    tgt_counter = Counter()
    for sent in sentence_pairs:
        src_counter.update(sent.source)
        tgt_counter.update(sent.target)

    def build(counter):
        items = counter.most_common(freq_cutoff) if freq_cutoff is not None else sorted(counter.items())
        tokens = [token for token, _ in items]
        return {token: i for i, token in enumerate(tokens)}

    return build(src_counter), build(tgt_counter)


def tokenize_sents(sentence_pairs: List[SentencePair], source_dict, target_dict) -> List[TokenizedSentencePair]:
    """Transform token strings to vocabulary indices; skip empty-after-filtering pairs."""
    result = []
    for sent in sentence_pairs:
        src = np.array([source_dict[t] for t in sent.source if t in source_dict], dtype=np.int32)
        tgt = np.array([target_dict[t] for t in sent.target if t in target_dict], dtype=np.int32)
        if len(src) > 0 and len(tgt) > 0:
            result.append(TokenizedSentencePair(src, tgt))
    return result
