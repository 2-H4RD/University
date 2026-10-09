from abc import ABC, abstractmethod
from itertools import product
from typing import Dict, List, Tuple

import numpy as np

from preprocessing import TokenizedSentencePair


class BaseAligner(ABC):
    @abstractmethod
    def fit(self, parallel_corpus: List[TokenizedSentencePair]):
        pass

    @abstractmethod
    def align(self, sentences: List[TokenizedSentencePair]) -> List[List[Tuple[int, int]]]:
        pass


class DiceAligner(BaseAligner):
    def __init__(self, num_source_words: int, num_target_words: int, threshold=0.5):
        self.cooc = np.zeros((num_source_words, num_target_words), dtype=np.uint32)
        self.dice_scores = None
        self.threshold = threshold

    def fit(self, parallel_corpus):
        for sentence in parallel_corpus:
            for source_token in np.unique(sentence.source_tokens):
                for target_token in np.unique(sentence.target_tokens):
                    self.cooc[source_token, target_token] += 1
        denom = self.cooc.sum(0, keepdims=True) + self.cooc.sum(1, keepdims=True)
        self.dice_scores = np.divide(2 * self.cooc.astype(np.float32), denom,
                                     out=np.zeros_like(self.cooc, dtype=np.float32), where=denom != 0)
        return []

    def align(self, sentences):
        result = []
        for sentence in sentences:
            alignment = []
            for (i, source_token), (j, target_token) in product(enumerate(sentence.source_tokens, 1), enumerate(sentence.target_tokens, 1)):
                if self.dice_scores[source_token, target_token] > self.threshold:
                    alignment.append((i, j))
            result.append(alignment)
        return result


class WordAligner(BaseAligner):
    def __init__(self, num_source_words, num_target_words, num_iters):
        self.num_source_words = num_source_words
        self.num_target_words = num_target_words
        self.translation_probs = np.full((num_source_words, num_target_words), 1 / num_target_words, dtype=np.float32)
        self.num_iters = num_iters

    def _e_step(self, parallel_corpus: List[TokenizedSentencePair]) -> List[np.array]:
        posteriors = []
        for sent in parallel_corpus:
            scores = self.translation_probs[np.ix_(sent.source_tokens, sent.target_tokens)].astype(np.float64)
            denom = scores.sum(axis=0, keepdims=True)
            posterior = np.divide(scores, denom, out=np.full_like(scores, 1 / len(sent.source_tokens)), where=denom > 0)
            posteriors.append(posterior.astype(np.float32))
        return posteriors

    def _compute_elbo(self, parallel_corpus: List[TokenizedSentencePair], posteriors: List[np.array]) -> float:
        elbo = 0.0
        eps = 1e-12
        for sent, posterior in zip(parallel_corpus, posteriors):
            theta = self.translation_probs[np.ix_(sent.source_tokens, sent.target_tokens)]
            log_prior = -np.log(len(sent.source_tokens))
            elbo += np.sum(posterior * (np.log(theta + eps) + log_prior - np.log(posterior + eps)))
        return float(elbo)

    def _m_step(self, parallel_corpus: List[TokenizedSentencePair], posteriors: List[np.array]):
        counts = np.zeros_like(self.translation_probs, dtype=np.float32)
        for sent, posterior in zip(parallel_corpus, posteriors):
            for src_pos, src_token in enumerate(sent.source_tokens):
                np.add.at(counts[src_token], sent.target_tokens, posterior[src_pos])

        row_sums = counts.sum(axis=1, keepdims=True)
        self.translation_probs = np.divide(counts, row_sums,
                                           out=np.full_like(counts, 1 / self.num_target_words, dtype=np.float32),
                                           where=row_sums > 0)
        return self._compute_elbo(parallel_corpus, posteriors)

    def fit(self, parallel_corpus):
        history = []
        for _ in range(self.num_iters):
            posteriors = self._e_step(parallel_corpus)
            history.append(self._m_step(parallel_corpus, posteriors))
        return history

    def align(self, sentences):
        result = []
        for sent in sentences:
            scores = self.translation_probs[np.ix_(sent.source_tokens, sent.target_tokens)]
            best_src_pos = scores.argmax(axis=0)
            result.append([(int(src_pos + 1), int(tgt_pos + 1)) for tgt_pos, src_pos in enumerate(best_src_pos)])
        return result


class WordPositionAligner(WordAligner):
    def __init__(self, num_source_words, num_target_words, num_iters):
        super().__init__(num_source_words, num_target_words, num_iters)
        self.alignment_probs: Dict[Tuple[int, int], np.ndarray] = {}

    def _get_probs_for_lengths(self, src_length: int, tgt_length: int):
        key = (src_length, tgt_length)
        if key not in self.alignment_probs:
            self.alignment_probs[key] = np.full((src_length, tgt_length), 1 / src_length, dtype=np.float32)
        return self.alignment_probs[key]

    def _e_step(self, parallel_corpus):
        posteriors = []
        for sent in parallel_corpus:
            theta = self.translation_probs[np.ix_(sent.source_tokens, sent.target_tokens)].astype(np.float64)
            phi = self._get_probs_for_lengths(len(sent.source_tokens), len(sent.target_tokens)).astype(np.float64)
            scores = theta * phi
            denom = scores.sum(axis=0, keepdims=True)
            posterior = np.divide(scores, denom, out=np.full_like(scores, 1 / len(sent.source_tokens)), where=denom > 0)
            posteriors.append(posterior.astype(np.float32))
        return posteriors

    def _compute_elbo(self, parallel_corpus, posteriors):
        elbo = 0.0
        eps = 1e-12
        for sent, posterior in zip(parallel_corpus, posteriors):
            theta = self.translation_probs[np.ix_(sent.source_tokens, sent.target_tokens)]
            phi = self._get_probs_for_lengths(len(sent.source_tokens), len(sent.target_tokens))
            elbo += np.sum(posterior * (np.log(theta + eps) + np.log(phi + eps) - np.log(posterior + eps)))
        return float(elbo)

    def _m_step(self, parallel_corpus, posteriors):
        counts = np.zeros_like(self.translation_probs, dtype=np.float32)
        alignment_counts = {}

        for sent, posterior in zip(parallel_corpus, posteriors):
            for src_pos, src_token in enumerate(sent.source_tokens):
                np.add.at(counts[src_token], sent.target_tokens, posterior[src_pos])

            key = (len(sent.source_tokens), len(sent.target_tokens))
            if key not in alignment_counts:
                alignment_counts[key] = np.zeros((key[0], key[1]), dtype=np.float32)
            alignment_counts[key] += posterior

        row_sums = counts.sum(axis=1, keepdims=True)
        self.translation_probs = np.divide(counts, row_sums,
                                           out=np.full_like(counts, 1 / self.num_target_words, dtype=np.float32),
                                           where=row_sums > 0)

        for key, mat in alignment_counts.items():
            col_sums = mat.sum(axis=0, keepdims=True)
            self.alignment_probs[key] = np.divide(mat, col_sums,
                                                  out=np.full_like(mat, 1 / key[0], dtype=np.float32),
                                                  where=col_sums > 0)

        return self._compute_elbo(parallel_corpus, posteriors)

    def align(self, sentences):
        result = []
        for sent in sentences:
            theta = self.translation_probs[np.ix_(sent.source_tokens, sent.target_tokens)]
            phi = self._get_probs_for_lengths(len(sent.source_tokens), len(sent.target_tokens))
            scores = theta * phi
            best_src_pos = scores.argmax(axis=0)
            result.append([(int(src_pos + 1), int(tgt_pos + 1)) for tgt_pos, src_pos in enumerate(best_src_pos)])
        return result
