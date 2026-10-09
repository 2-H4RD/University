from __future__ import annotations

from typing import Dict, List, Sequence, Tuple
import random

import config as cfg
import stage_1 as st1
import stage_2 as st2
import stage_3 as st3


POP_SIZE = cfg.POP_SIZE
PSI = cfg.PSI
MAX_ITERATIONS = cfg.MAX_ITERATIONS
TARGET_ELITE_RATIO = cfg.TARGET_ELITE_RATIO
ELITE_KEEP_RATIO = cfg.ELITE_KEEP_RATIO
STAGNATION_LIMIT = cfg.STAGNATION_LIMIT
MUTATION_PROBABILITY = cfg.MUTATION_PROBABILITY
ADAPTIVE_MUTATION_START_ELITE_RATIO = cfg.ADAPTIVE_MUTATION_START_ELITE_RATIO
ADAPTIVE_MUTATION_MAX_PROBABILITY = cfg.ADAPTIVE_MUTATION_MAX_PROBABILITY
PRINT_ITERATION_SUMMARY = cfg.PRINT_ITERATION_SUMMARY
SELECTION_GROUP_SIZE = cfg.SELECTION_GROUP_SIZE
PARENTS_PER_GROUP = cfg.PARENTS_PER_GROUP
SELECTION_CYCLES = cfg.SELECTION_CYCLES


# ------------------------------------------------------------
# ОБЩИЕ ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------------------------------------
def initialize_random_seed(seed: int | None = cfg.RANDOM_SEED) -> None:
    if seed is not None:
        random.seed(seed)



def top_indices_by_fitness(fitness_list: Sequence[float], count: int) -> List[int]:
    if count <= 0:
        return []
    count = min(count, len(fitness_list))
    indices = list(range(len(fitness_list)))
    indices.sort(key=lambda i: fitness_list[i], reverse=True)
    return indices[:count]



def preserve_elite_individuals(
    population: Sequence[st1.Individual],
    fitness_list: Sequence[float],
    count: int,
) -> List[st1.Individual]:
    indices = top_indices_by_fitness(fitness_list, count)
    return [st1.clone_individual(population[i]) for i in indices]



def elite_keep_count_from_ratio(population_size: int, elite_keep_ratio: float = ELITE_KEEP_RATIO) -> int:
    if not (0.0 <= elite_keep_ratio <= 1.0):
        raise ValueError("elite_keep_ratio должен быть в диапазоне [0, 1]")
    return max(0, min(population_size, int(round(population_size * elite_keep_ratio))))



def adaptive_mutation_probability(
    elite_ratio: float,
    base_probability: float = MUTATION_PROBABILITY,
    start_elite_ratio: float = ADAPTIVE_MUTATION_START_ELITE_RATIO,
    max_probability: float = ADAPTIVE_MUTATION_MAX_PROBABILITY,
    target_elite_ratio: float = TARGET_ELITE_RATIO,
) -> float:
    if elite_ratio <= start_elite_ratio or target_elite_ratio <= start_elite_ratio:
        return base_probability
    if elite_ratio >= target_elite_ratio:
        return max_probability

    scale = (elite_ratio - start_elite_ratio) / (target_elite_ratio - start_elite_ratio)
    return base_probability + scale * (max_probability - base_probability)



def compose_next_population(
    current_population: Sequence[st1.Individual],
    fitness_list: Sequence[float],
    mutation_probability: float,
    elite_keep_ratio: float = ELITE_KEEP_RATIO,
    selection_group_size: int = SELECTION_GROUP_SIZE,
    parents_per_group: int = PARENTS_PER_GROUP,
    selection_cycles: int = SELECTION_CYCLES,
) -> Tuple[List[st1.Individual], int]:
    elite_keep_count = elite_keep_count_from_ratio(len(current_population), elite_keep_ratio=elite_keep_ratio)
    elite = preserve_elite_individuals(current_population, fitness_list, elite_keep_count)

    offspring_target_size = len(current_population) - len(elite)
    if offspring_target_size <= 0:
        return st1.clone_population(elite), 0
    if offspring_target_size % 2 != 0:
        offspring_target_size += 1

    parent_population, completed_cycles = st3.build_parent_population(
        population=current_population,
        fitness_list=fitness_list,
        target_size=offspring_target_size,
        selection_group_size=selection_group_size,
        parents_per_group=parents_per_group,
        selection_cycles=selection_cycles,
    )
    offspring = st3.build_offspring_population(
        parent_population=parent_population,
        mutation_probability=mutation_probability,
    )

    next_population = elite + offspring[: len(current_population) - len(elite)]
    return next_population, completed_cycles


# ------------------------------------------------------------
# ЗАДАЧА 1: ПАРЕТО-ОПТИМАЛЬНЫЕ РЕШЕНИЯ
# ------------------------------------------------------------
def run_pareto_ga(
    pop_size: int = POP_SIZE,
    max_iterations: int = MAX_ITERATIONS,
    target_elite_ratio: float = TARGET_ELITE_RATIO,
    elite_keep_ratio: float = ELITE_KEEP_RATIO,
    psi: float = PSI,
) -> Dict[str, object]:
    population = st1.generate_initial_population(pop_size=pop_size)
    pareto_archive: List[st1.Individual] = []
    elite_candidates_archive: List[st1.Individual] = []
    history: List[dict] = []

    best_archive_size = 0
    iterations_without_improvement = 0
    last_completed_cycles = 0

    for iteration in range(1, max_iterations + 1):
        payoff_pairs, dominator_counts, phi_list, elite_idx = st2.rank_population_pareto(population, psi=psi)
        current_elites = [population[index] for index in elite_idx]

        elite_candidates_archive.extend(st1.clone_population(current_elites))
        pareto_archive = st2.merge_and_prune_pareto_archive(pareto_archive, current_elites, psi=psi)

        elite_count = len(elite_idx)
        elite_ratio = elite_count / len(population) if population else 0.0
        current_mutation_probability = adaptive_mutation_probability(elite_ratio=elite_ratio)

        archive_size = len(pareto_archive)
        best_phi = max(phi_list) if phi_list else 0.0

        if archive_size > best_archive_size:
            best_archive_size = archive_size
            iterations_without_improvement = 0
        else:
            iterations_without_improvement += 1

        
        stop_reason = None
        selection_cycles_completed = last_completed_cycles 
        if elite_ratio >= target_elite_ratio:
            stop_reason = "target_elite_ratio"
        elif iterations_without_improvement >= STAGNATION_LIMIT:
            stop_reason = "stagnation"
        else:
            population, selection_cycles_completed = compose_next_population(
                current_population=population,
                fitness_list=phi_list,
                mutation_probability=current_mutation_probability,
                elite_keep_ratio=elite_keep_ratio,
                selection_group_size=SELECTION_GROUP_SIZE,
                parents_per_group=PARENTS_PER_GROUP,
                selection_cycles=SELECTION_CYCLES,
            )
            last_completed_cycles = selection_cycles_completed
            
        history.append(
            {
                "iteration": iteration,
                "full_ga_cycles_completed": selection_cycles_completed,
                "elite_count": elite_count,
                "elite_ratio": elite_ratio,
                "archive_size": archive_size,
                "best_phi": best_phi,
                "mutation_probability": current_mutation_probability,
            }
        )

        if PRINT_ITERATION_SUMMARY:
            print(
                f"Итерация {iteration}: полных циклов ГА завершено = {selection_cycles_completed}, "
                f"элитных точек = {elite_count} из {len(payoff_pairs)} ({elite_ratio * 100:.2f}%)"
            )

        if stop_reason is not None:
            break

    archive_payoffs = st2.build_payoff_pairs(pareto_archive)
    archive_strategies = [st1.decode_individual_to_strategy_profile(individual) for individual in pareto_archive]

    sorted_elite_candidates: List[st1.Individual] = []
    sorted_elite_payoffs: List[Tuple[float, float]] = []
    sorted_elite_fitness: List[float] = []
    if elite_candidates_archive:
        unique_candidates_map = {}
        for individual in elite_candidates_archive:
            strategy_a, strategy_b, u_a, u_b = st2.decode_and_evaluate(individual)
            key = tuple(round(value, cfg.ARCHIVE_ROUND_DIGITS) for value in (u_a, u_b, *strategy_a, *strategy_b))
            unique_candidates_map[key] = st1.clone_individual(individual)
        unique_candidates = list(unique_candidates_map.values())

        _, _, candidate_phi_list, _ = st2.rank_population_pareto(unique_candidates, psi=psi)
        sorted_elite_candidates = st2.sort_population_by_fitness_desc(unique_candidates, candidate_phi_list)
        sorted_elite_payoffs = st2.build_payoff_pairs(sorted_elite_candidates)
        sorted_elite_fitness = sorted(candidate_phi_list, reverse=True)

    return {
        "final_population": population,
        "pareto_archive": pareto_archive,
        "pareto_payoffs": archive_payoffs,
        "pareto_strategies": archive_strategies,
        "elite_candidates_sorted": sorted_elite_candidates,
        "elite_candidates_payoffs": sorted_elite_payoffs,
        "elite_candidates_fitness": sorted_elite_fitness,
        "history": history,
    }
