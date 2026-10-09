from __future__ import annotations

from typing import List, Sequence, Tuple
import math
import random

import config as cfg
import stage_1 as st1


SELECTION_GROUP_SIZE = cfg.SELECTION_GROUP_SIZE
PARENTS_PER_GROUP = cfg.PARENTS_PER_GROUP
SELECTION_CYCLES = cfg.SELECTION_CYCLES
MUTATION_PROBABILITY = cfg.MUTATION_PROBABILITY


# ------------------------------------------------------------
# ТУРНИРНАЯ СЕЛЕКЦИЯ ПО ГРУППАМ
# ------------------------------------------------------------
def _validate_selection_parameters(
    population_size: int,
    selection_group_size: int,
    parents_per_group: int,
) -> None:
    if population_size <= 0:
        raise ValueError("Размер популяции должен быть > 0")
    if selection_group_size <= 0:
        raise ValueError("selection_group_size должен быть > 0")
    if parents_per_group <= 0:
        raise ValueError("parents_per_group должен быть > 0")
    if population_size % selection_group_size != 0:
        raise ValueError(
            "Размер популяции должен делиться на selection_group_size без остатка "
            "для группового турнирного отбора"
        )
    if parents_per_group > selection_group_size:
        raise ValueError("parents_per_group не может быть больше selection_group_size")


def perform_group_tournament_cycle(
    population: Sequence[st1.Individual],
    fitness_list: Sequence[float],
    selection_group_size: int = SELECTION_GROUP_SIZE,
    parents_per_group: int = PARENTS_PER_GROUP,
) -> List[st1.Individual]:
    if len(population) != len(fitness_list):
        raise ValueError("Размер population и fitness_list должен совпадать")

    population_size = len(population)
    _validate_selection_parameters(population_size, selection_group_size, parents_per_group)

    shuffled_indices = list(range(population_size))
    random.shuffle(shuffled_indices)

    parents: List[st1.Individual] = []
    for start in range(0, population_size, selection_group_size):
        group_indices = shuffled_indices[start : start + selection_group_size]
        group_indices.sort(key=lambda index: fitness_list[index], reverse=True)

        for winner_index in group_indices[:parents_per_group]:
            parents.append(st1.clone_individual(population[winner_index]))

    return parents


def build_parent_population(
    population: Sequence[st1.Individual],
    fitness_list: Sequence[float],
    target_size: int,
    selection_group_size: int = SELECTION_GROUP_SIZE,
    parents_per_group: int = PARENTS_PER_GROUP,
    selection_cycles: int = SELECTION_CYCLES,
) -> Tuple[List[st1.Individual], int]:
    if target_size <= 0:
        raise ValueError("target_size должен быть > 0")
    if not population:
        raise ValueError("Популяция пуста")

    population_size = len(population)
    _validate_selection_parameters(population_size, selection_group_size, parents_per_group)

    groups_count = population_size // selection_group_size
    parents_per_cycle = groups_count * parents_per_group
    required_cycles = math.ceil(target_size / parents_per_cycle)
    total_cycles = max(selection_cycles, required_cycles)

    parents: List[st1.Individual] = []
    completed_cycles = 0
    for _ in range(total_cycles):
        parents.extend(
            perform_group_tournament_cycle(
                population=population,
                fitness_list=fitness_list,
                selection_group_size=selection_group_size,
                parents_per_group=parents_per_group,
            )
        )
        completed_cycles += 1
        if len(parents) >= target_size:
            break

    if len(parents) < target_size:
        raise RuntimeError("Не удалось сформировать требуемую популяцию родителей")

    return parents[:target_size], completed_cycles


# ------------------------------------------------------------
# ТРЁХТОЧЕЧНЫЙ КРОССОВЕР
# ------------------------------------------------------------
def generate_crossover_points_for_pair(individual: st1.Individual) -> Tuple[int, int, int]:
    if individual.genotype_length < 4:
        raise ValueError("Хромосома слишком короткая для трёхточечного кроссовера")

    point2 = individual.split_point
    if point2 <= 1 or point2 >= individual.genotype_length - 1:
        raise ValueError("Невозможно выбрать корректные точки кроссовера")

    point1 = random.randint(1, point2 - 1)
    point3 = random.randint(point2 + 1, individual.genotype_length - 1)
    return point1, point2, point3



def three_point_crossover(
    parent1: st1.Individual,
    parent2: st1.Individual,
    point1: int,
    point2: int,
    point3: int,
) -> Tuple[List[int], List[int]]:
    if parent1.genotype_length != parent2.genotype_length:
        raise ValueError("Длины хромосом родителей не совпадают")
    if not (1 <= point1 < point2 < point3 < parent1.genotype_length):
        raise ValueError("Некорректные точки кроссовера")

    g1 = parent1.genotype
    g2 = parent2.genotype

    child1 = g2[:point1] + g1[point1:point2] + g2[point2:point3] + g1[point3:]
    child2 = g1[:point1] + g2[point1:point2] + g1[point2:point3] + g2[point3:]
    return child1, child2


# ------------------------------------------------------------
# МУТАЦИЯ
# ------------------------------------------------------------
def mutate_genotype(
    genotype: Sequence[int],
    mutation_probability: float = MUTATION_PROBABILITY,
) -> List[int]:
    if not (0.0 <= mutation_probability <= 1.0):
        raise ValueError("mutation_probability должен быть в диапазоне [0, 1]")

    mutated = list(genotype)
    if random.random() < mutation_probability:
        bit_index = random.randrange(len(mutated))
        mutated[bit_index] = 1 - mutated[bit_index]
    return mutated


# ------------------------------------------------------------
# ФОРМИРОВАНИЕ ПОТОМКОВ
# ------------------------------------------------------------
def build_offspring_population(
    parent_population: Sequence[st1.Individual],
    mutation_probability: float = MUTATION_PROBABILITY,
) -> List[st1.Individual]:
    if not parent_population:
        raise ValueError("Популяция родителей пуста")
    if len(parent_population) % 2 != 0:
        raise ValueError("Размер parent_population должен быть чётным")

    shuffled_parents = list(parent_population)
    random.shuffle(shuffled_parents)

    offspring: List[st1.Individual] = []
    for i in range(0, len(shuffled_parents), 2):
        parent1 = shuffled_parents[i]
        parent2 = shuffled_parents[i + 1]

        point1, point2, point3 = generate_crossover_points_for_pair(parent1)
        child1_bits, child2_bits = three_point_crossover(parent1, parent2, point1, point2, point3)

        child1_bits = mutate_genotype(child1_bits, mutation_probability=mutation_probability)
        child2_bits = mutate_genotype(child2_bits, mutation_probability=mutation_probability)

        child1 = st1.Individual(
            genotype=child1_bits,
            bits_per_gene=parent1.bits_per_gene,
            genes_per_player_a=parent1.genes_per_player_a,
            genes_per_player_b=parent1.genes_per_player_b,
        )
        child2 = st1.Individual(
            genotype=child2_bits,
            bits_per_gene=parent2.bits_per_gene,
            genes_per_player_a=parent2.genes_per_player_a,
            genes_per_player_b=parent2.genes_per_player_b,
        )

        offspring.append(child1)
        offspring.append(child2)

    return offspring
