from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence, Tuple
import random

import config as cfg


@dataclass
class Individual:
    """Генотип одной особи.

    Хромосома состоит из двух блоков:
    1) веса смешанной стратегии игрока A;
    2) веса смешанной стратегии игрока B.

    Каждый вес кодируется бинарным кодом Грея фиксированной длины.
    """

    genotype: List[int]
    bits_per_gene: int = cfg.BITS_PER_GENE
    genes_per_player_a: int = cfg.GENES_PER_PLAYER_A
    genes_per_player_b: int = cfg.GENES_PER_PLAYER_B

    @property
    def genes_count(self) -> int:
        return self.genes_per_player_a + self.genes_per_player_b

    @property
    def genotype_length(self) -> int:
        return self.genes_count * self.bits_per_gene

    @property
    def split_point(self) -> int:
        return self.genes_per_player_a * self.bits_per_gene

    @property
    def gray_block_a(self) -> List[int]:
        return self.genotype[: self.split_point]

    @property
    def gray_block_b(self) -> List[int]:
        return self.genotype[self.split_point :]


# ------------------------------------------------------------
# БАЗОВЫЕ ФУНКЦИИ ДЛЯ КОДА ГРЕЯ
# ------------------------------------------------------------
def int_to_gray_int(value: int) -> int:
    return value ^ (value >> 1)


def int_to_bits(value: int, bits_count: int) -> List[int]:
    return [((value >> shift) & 1) for shift in range(bits_count - 1, -1, -1)]


def gray_int_to_bits(gray_value: int, bits_count: int) -> List[int]:
    return int_to_bits(gray_value, bits_count)


def gray_bits_to_int(gray_bits: Sequence[int]) -> int:
    gray_value = 0
    for bit in gray_bits:
        gray_value = (gray_value << 1) | int(bit)

    binary_value = gray_value
    shifted = gray_value >> 1
    while shifted > 0:
        binary_value ^= shifted
        shifted >>= 1

    return binary_value


# ------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ РАБОТЫ С ХРОМОСОМОЙ
# ------------------------------------------------------------
def chunk_bits(bits: Sequence[int], chunk_size: int) -> List[List[int]]:
    if chunk_size <= 0:
        raise ValueError("chunk_size должен быть > 0")
    if len(bits) % chunk_size != 0:
        raise ValueError("Длина массива битов должна делиться на размер чанка без остатка")
    return [list(bits[i : i + chunk_size]) for i in range(0, len(bits), chunk_size)]


def normalize_weights(weights: Sequence[float]) -> List[float]:
    total = sum(weights)
    if total <= 0.0:
        if len(weights) == 0:
            return []
        uniform = 1.0 / len(weights)
        return [uniform for _ in weights]
    return [value / total for value in weights]


def decode_gray_gene(gray_gene_bits: Sequence[int]) -> int:
    return gray_bits_to_int(gray_gene_bits)


def decode_gray_block_to_weights(gray_block_bits: Sequence[int], bits_per_gene: int) -> List[float]:
    genes = chunk_bits(gray_block_bits, bits_per_gene)
    return [float(decode_gray_gene(gene_bits)) for gene_bits in genes]


def decode_individual_to_strategy_profile(individual: Individual) -> Tuple[List[float], List[float]]:
    weights_a = decode_gray_block_to_weights(individual.gray_block_a, individual.bits_per_gene)
    weights_b = decode_gray_block_to_weights(individual.gray_block_b, individual.bits_per_gene)
    strategy_a = normalize_weights(weights_a)
    strategy_b = normalize_weights(weights_b)
    return strategy_a, strategy_b


def decode_individual_to_player_a_strategy(individual: Individual) -> List[float]:
    strategy_a, _ = decode_individual_to_strategy_profile(individual)
    return strategy_a


def decode_individual_to_player_b_strategy(individual: Individual) -> List[float]:
    _, strategy_b = decode_individual_to_strategy_profile(individual)
    return strategy_b


# ------------------------------------------------------------
# ГЕНЕРАЦИЯ И КЛОНИРОВАНИЕ
# ------------------------------------------------------------
def make_individual_from_integer_genes(
    gene_values_a: Sequence[int],
    gene_values_b: Sequence[int],
    bits_per_gene: int = cfg.BITS_PER_GENE,
) -> Individual:
    genotype: List[int] = []

    max_level = (1 << bits_per_gene) - 1
    for value in list(gene_values_a) + list(gene_values_b):
        if not (0 <= int(value) <= max_level):
            raise ValueError(f"Значение гена {value} выходит за диапазон [0, {max_level}]")
        gray_value = int_to_gray_int(int(value))
        genotype.extend(gray_int_to_bits(gray_value, bits_per_gene))

    return Individual(
        genotype=genotype,
        bits_per_gene=bits_per_gene,
        genes_per_player_a=len(gene_values_a),
        genes_per_player_b=len(gene_values_b),
    )


def random_individual(
    bits_per_gene: int = cfg.BITS_PER_GENE,
    genes_per_player_a: int = cfg.GENES_PER_PLAYER_A,
    genes_per_player_b: int = cfg.GENES_PER_PLAYER_B,
) -> Individual:
    genotype_length = (genes_per_player_a + genes_per_player_b) * bits_per_gene
    genotype = [random.randint(0, 1) for _ in range(genotype_length)]
    return Individual(
        genotype=genotype,
        bits_per_gene=bits_per_gene,
        genes_per_player_a=genes_per_player_a,
        genes_per_player_b=genes_per_player_b,
    )


def generate_initial_population(
    pop_size: int = cfg.POP_SIZE,
    bits_per_gene: int = cfg.BITS_PER_GENE,
    genes_per_player_a: int = cfg.GENES_PER_PLAYER_A,
    genes_per_player_b: int = cfg.GENES_PER_PLAYER_B,
) -> List[Individual]:
    if pop_size <= 0:
        raise ValueError("pop_size должен быть > 0")
    return [
        random_individual(
            bits_per_gene=bits_per_gene,
            genes_per_player_a=genes_per_player_a,
            genes_per_player_b=genes_per_player_b,
        )
        for _ in range(pop_size)
    ]


def clone_individual(individual: Individual) -> Individual:
    return Individual(
        genotype=list(individual.genotype),
        bits_per_gene=individual.bits_per_gene,
        genes_per_player_a=individual.genes_per_player_a,
        genes_per_player_b=individual.genes_per_player_b,
    )


def clone_population(population: Iterable[Individual]) -> List[Individual]:
    return [clone_individual(individual) for individual in population]


# ------------------------------------------------------------
# СЕРВИСНЫЙ ВЫВОД
# ------------------------------------------------------------
def bits_to_string(bits: Sequence[int]) -> str:
    return "".join(str(int(bit)) for bit in bits)


def format_probability_vector(values: Sequence[float], digits: int = 6) -> str:
    return "[" + ", ".join(f"{value:.{digits}f}" for value in values) + "]"
