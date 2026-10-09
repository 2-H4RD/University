from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
from tabulate import tabulate

import config as cfg
import stage_1 as st1
import stage_2 as st2
import stage_3 as st3


# ============================================================
# НАСТРОЙКИ СТАДИИ 4
# ============================================================
TARGET_ELITE_RATIO = cfg.TARGET_ELITE_RATIO
MAX_ITERATIONS = cfg.MAX_ITERATIONS
ELITE_KEEP_RATIO = cfg.ELITE_KEEP_RATIO

SELECTION_CYCLES = cfg.SELECTION_CYCLES
MUTATION_PROBABILITY = cfg.MUTATION_PROBABILITY
ADAPTIVE_MUTATION_START_ELITE_RATIO = cfg.ADAPTIVE_MUTATION_START_ELITE_RATIO
ADAPTIVE_MUTATION_MAX_PROBABILITY = cfg.ADAPTIVE_MUTATION_MAX_PROBABILITY

PSI = cfg.PSI
ELITE_RATIO_PLOT_THRESHOLDS = tuple(cfg.ELITE_RATIO_PLOT_THRESHOLDS)
# ============================================================


# ------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------------------------------------
def clone_individual(individual: st1.Individual) -> st1.Individual:
    return st1.Individual(
        genotype=individual.genotype.copy(),
        bits_per_var=individual.bits_per_var,
    )


def clone_population(population: List[st1.Individual]) -> List[st1.Individual]:
    return [clone_individual(individual) for individual in population]


def extract_elite_population(
    population: List[st1.Individual],
    elite_idx: List[int],
) -> List[st1.Individual]:
    elite_population = []
    for index in elite_idx:
        elite_population.append(population[index])
    return elite_population


def select_best_survivors(
    population: List[st1.Individual],
    objs: List[Tuple[float, float]],
    phi_list: List[float],
    keep_ratio: float = ELITE_KEEP_RATIO,
) -> List[st1.Individual]:
    if not population:
        return []

    if not (0.0 <= keep_ratio <= 1.0):
        raise ValueError("keep_ratio должен быть в диапазоне (0, 1].")

    keep_count = int(len(population) * keep_ratio)
    if keep_count <= 0:
        keep_count = 1
    if keep_count > len(population):
        keep_count = len(population)

    ranked_indices = list(range(len(population)))
    ranked_indices.sort(
        key=lambda i: (
            -phi_list[i],
            objs[i][0] + objs[i][1],
            objs[i][0],
            objs[i][1],
        )
    )

    survivors = []
    for index in ranked_indices[:keep_count]:
        survivors.append(clone_individual(population[index]))

    return survivors


def compute_adaptive_mutation_probability(
    elite_ratio: float,
    base_probability: float = MUTATION_PROBABILITY,
    start_elite_ratio: float = ADAPTIVE_MUTATION_START_ELITE_RATIO,
    target_elite_ratio: float = TARGET_ELITE_RATIO,
    max_probability: float = ADAPTIVE_MUTATION_MAX_PROBABILITY,
) -> float:
    """
    Адаптивная мутация (вариант C):
    - до start_elite_ratio используется базовая вероятность;
    - дальше вероятность линейно растёт вместе с долей элитных точек;
    - к моменту достижения target_elite_ratio достигается max_probability.
    """
    if not (0.0 <= elite_ratio <= 1.0):
        raise ValueError("elite_ratio должен быть в диапазоне [0, 1].")
    if not (0.0 <= base_probability <= 1.0):
        raise ValueError("base_probability должен быть в диапазоне [0, 1].")
    if not (0.0 <= start_elite_ratio <= 1.0):
        raise ValueError("start_elite_ratio должен быть в диапазоне [0, 1].")
    if not (0.0 < target_elite_ratio <= 1.0):
        raise ValueError("target_elite_ratio должен быть в диапазоне (0, 1].")
    if not (0.0 <= max_probability <= 1.0):
        raise ValueError("max_probability должен быть в диапазоне [0, 1].")

    max_probability = max(max_probability, base_probability)

    if elite_ratio <= start_elite_ratio:
        return base_probability

    if target_elite_ratio <= start_elite_ratio:
        return max_probability

    if elite_ratio >= target_elite_ratio:
        return max_probability

    progress = (elite_ratio - start_elite_ratio) / (target_elite_ratio - start_elite_ratio)
    return base_probability + progress * (max_probability - base_probability)


def print_stage4_history(history: List[dict]) -> None:
    rows = []

    for item in history:
        rows.append({
            "Итерация": item["iteration"],
            "Размер популяции": item["population_size"],
            "Доля элитных": f"{item['elite_ratio']:.4f}",
            "k_group": item["k_group"],
            "Родителей из группы": item["parents_per_group"],
            "Вероятность мутации": f"{item['mutation_probability']:.4f}",
        })
    print(tabulate(rows, headers="keys", tablefmt="grid", showindex=False))


def print_first_elite_points(
    elite_points: List[st1.Individual],
    limit: int = 50,
) -> None:
    print(f"\nПервые {min(limit, len(elite_points))} точек из массива all_elites (Phi = 1):")
    st1.print_population(elite_points, limit=limit)


def plot_initial_population_in_decision_space(
    population: List[st1.Individual],
    x1_bounds: Tuple[float, float],
    x2_bounds: Tuple[float, float],
) -> None:
    st1.plot_population(
        population,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
        title="Этап 1: начальная популяция в пространстве x1, x2",
    )


def plot_population_with_pareto_front(
    objs: List[Tuple[float, float]],
    elite_idx: List[int],
    title: str,
    show_all_label: str = "все точки",
    show_elite_label: str = "Парето-оптимальные точки",
) -> None:
    all_f1 = [point[0] for point in objs]
    all_f2 = [point[1] for point in objs]
    elite_f1 = [objs[i][0] for i in elite_idx]
    elite_f2 = [objs[i][1] for i in elite_idx]

    plt.figure(figsize=(10, 8))
    plt.scatter(all_f1, all_f2, s=18, alpha=0.9, color="blue", label=show_all_label, zorder=1)
    plt.scatter(
        elite_f1,
        elite_f2,
        s=34,
        alpha=1.0,
        color="green",
        edgecolors="black",
        linewidths=0.35,
        label=show_elite_label,
        zorder=3,
    )
    plt.title(title)
    plt.xlabel("f1 (min)")
    plt.ylabel("f2 (min)")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()


def plot_threshold_populations(
    threshold_snapshots: Dict[float, dict],
    thresholds: Tuple[float, ...],
) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    axes_flat = axes.flatten()

    for axis, threshold in zip(axes_flat, thresholds):
        snapshot = threshold_snapshots.get(threshold)
        axis.grid(True, alpha=0.3)
        axis.set_xlabel("f1 (min)")
        axis.set_ylabel("f2 (min)")

        if snapshot is None:
            axis.set_title(f"Порог {threshold * 100:.0f}% не достигнут")
            axis.text(0.5, 0.5, "Популяция отсутствует", ha="center", va="center", transform=axis.transAxes)
            continue

        objs = snapshot["objs"]
        axis.scatter(
            [point[0] for point in objs],
            [point[1] for point in objs],
            s=16,
            alpha=0.9,
            color="blue",
            zorder=2,
        )
        axis.set_title(
            f"Первое поколение, преодолевшее {threshold * 100:.0f}%\n"
            f"итерация {snapshot['iteration']}, элитных {snapshot['elite_ratio'] * 100:.2f}%"
        )

    fig.suptitle("Популяции при достижении порогов доли элитных точек")
    fig.tight_layout()
    plt.show()


def plot_elite_ratio_dynamics(history: List[dict]) -> None:
    iterations = [item["iteration"] for item in history]
    elite_ratios = [item["elite_ratio"] * 100.0 for item in history]

    plt.figure(figsize=(11, 6))
    plt.plot(iterations, elite_ratios, marker="o")
    plt.title("СТАДИЯ 4: динамика роста доли элитных точек по поколениям")
    plt.xlabel("Номер поколения")
    plt.ylabel("Доля элитных точек, %")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


def save_threshold_snapshot_if_needed(
    threshold_snapshots: Dict[float, dict],
    thresholds: Tuple[float, ...],
    iteration: int,
    population: List[st1.Individual],
    objs: List[Tuple[float, float]],
    elite_ratio: float,
) -> None:
    for threshold in thresholds:
        if threshold not in threshold_snapshots and elite_ratio >= threshold:
            threshold_snapshots[threshold] = {
                "iteration": iteration,
                "population": clone_population(population),
                "objs": list(objs),
                "elite_ratio": elite_ratio,
            }


# ------------------------------------------------------------
# ПОЛНАЯ СТАДИЯ 4
# ------------------------------------------------------------
def run_stage4(
    pop_size: int = st1.POP_SIZE,
    bits_per_var: int = st1.BITS_PER_VAR,
    target_elite_ratio: float = TARGET_ELITE_RATIO,
    max_iterations: int = MAX_ITERATIONS,
    elite_keep_ratio: float = ELITE_KEEP_RATIO,
    k_group: Optional[int] = None,
    psi: float = PSI,
    selection_cycles: int = SELECTION_CYCLES,
    mutation_probability: float = MUTATION_PROBABILITY,
    elite_ratio_plot_thresholds: Tuple[float, ...] = ELITE_RATIO_PLOT_THRESHOLDS,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> Tuple[
    List[st1.Individual],
    List[st1.Individual],
    List[dict],
    Dict[float, dict],
    List[st1.Individual],
    List[Tuple[float, float]],
    List[int],
]:
    if pop_size <= 0:
        raise ValueError("pop_size должен быть > 0")
    if bits_per_var <= 0:
        raise ValueError("bits_per_var должен быть > 0")
    if not (0.0 <= target_elite_ratio <= 1.0):
        raise ValueError("target_elite_ratio должен быть в диапазоне (0, 1].")
    if not (0.0 <= elite_keep_ratio <= 1.0):
        raise ValueError("elite_keep_ratio должен быть в диапазоне (0, 1].")
    if max_iterations <= 0:
        raise ValueError("max_iterations должен быть > 0.")

    thresholds = tuple(sorted(elite_ratio_plot_thresholds))
    for threshold in thresholds:
        if not (0.0 < threshold <= 1.0):
            raise ValueError("Все пороги должны лежать в диапазоне (0, 1].")

    current_population = st1.generate_initial_population(
        pop_size=pop_size,
        bits_per_var=bits_per_var,
    )

    initial_population = clone_population(current_population)
    plot_initial_population_in_decision_space(initial_population, x1_bounds, x2_bounds)

    initial_objs, initial_b_list, initial_phi_list, initial_elite_idx = st2.rank_population_methodical(
        current_population,
        psi=psi,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )
    plot_population_with_pareto_front(
        initial_objs,
        initial_elite_idx,
        title="Этап 2: начальная популяция и Парето-оптимальные точки в пространстве f1, f2",
    )

    all_elites: List[st1.Individual] = []
    history: List[dict] = []
    threshold_snapshots: Dict[float, dict] = {}
    completed_ga_cycles = 0
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        if iteration == 1:
            objs, b_list, phi_list, elite_idx = initial_objs, initial_b_list, initial_phi_list, initial_elite_idx
        else:
            objs, b_list, phi_list, elite_idx = st2.rank_population_methodical(
                current_population,
                psi=psi,
                x1_bounds=x1_bounds,
                x2_bounds=x2_bounds,
            )

        elite_population = extract_elite_population(current_population, elite_idx)
        all_elites.extend(elite_population)
        elite_ratio = len(elite_population) / len(current_population)

        save_threshold_snapshot_if_needed(
            threshold_snapshots=threshold_snapshots,
            thresholds=thresholds,
            iteration=iteration,
            population=current_population,
            objs=objs,
            elite_ratio=elite_ratio,
        )

        print(
            f"Итерация {iteration}: "
            f"полных циклов ГА завершено = {completed_ga_cycles}, "
            f"элитных точек = {len(elite_population)} из {len(current_population)} "
            f"({elite_ratio * 100:.2f}%)"
        )

        current_mutation_probability = compute_adaptive_mutation_probability(
            elite_ratio=elite_ratio,
            base_probability=mutation_probability,
            start_elite_ratio=ADAPTIVE_MUTATION_START_ELITE_RATIO,
            target_elite_ratio=target_elite_ratio,
            max_probability=ADAPTIVE_MUTATION_MAX_PROBABILITY,
        )

        history_record = {
            "iteration": iteration,
            "population_size": len(current_population),
            "elite_count": len(elite_population),
            "elite_ratio": elite_ratio,
            "elite_preserved": 0,
            "k_group": "-",
            "parents_per_group": "-",
            "parent_population_size": "-",
            "mutation_probability": current_mutation_probability,
            "crossover_points": "-",
        }

        if elite_ratio >= target_elite_ratio:
            history.append(history_record)
            break

        elite_survivors = select_best_survivors(
            current_population,
            objs,
            phi_list,
            keep_ratio=elite_keep_ratio,
        )

        parent_population, selection_history, selected_k_group, parents_per_group = st3.collect_parents_over_cycles(
            initial_population=current_population,
            cycles=selection_cycles,
            k_group=k_group,
            psi=psi,
            x1_bounds=x1_bounds,
            x2_bounds=x2_bounds,
        )

        offspring_population, crossover_points = st3.build_offspring_population(
            parent_population=parent_population,
            mutation_probability=current_mutation_probability,
        )

        offspring_needed = len(current_population) - len(elite_survivors)
        if offspring_needed < 0:
            raise RuntimeError("Число элитных особей для переноса превышает размер популяции.")

        next_population = elite_survivors + offspring_population[:offspring_needed]

        if len(next_population) != len(current_population):
            raise RuntimeError(
                f"Размер новой популяции {len(next_population)} "
                f"не совпадает с ожидаемым {len(current_population)}."
            )

        history_record.update({
            "elite_preserved": len(elite_survivors),
            "k_group": selected_k_group,
            "parents_per_group": parents_per_group,
            "parent_population_size": len(parent_population),
            "mutation_probability": current_mutation_probability,
            "crossover_points": crossover_points,
        })
        history.append(history_record)

        current_population = next_population
        completed_ga_cycles += 1

    print(f"Всего завершено полных циклов ГА: {completed_ga_cycles}")

    if iteration == max_iterations and history[-1]["elite_ratio"] < target_elite_ratio:
        print(
            f"\nПредупреждение: достигнут предел MAX_ITERATIONS={max_iterations}, "
            f"но доля элитных точек не достигла {target_elite_ratio:.2f}."
        )

    if not all_elites:
        raise RuntimeError("Массив элитных точек пуст. Это нештатная ситуация.")

    return (
        current_population,
        all_elites,
        history,
        threshold_snapshots,
        initial_population,
        initial_objs,
        initial_elite_idx,
    )


# ------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------
if __name__ == "__main__":
    (
        final_population,
        all_elites,
        history,
        threshold_snapshots,
        initial_population,
        initial_objs,
        initial_elite_idx,
    ) = run_stage4(
        pop_size=st1.POP_SIZE,
        bits_per_var=st1.BITS_PER_VAR,
        target_elite_ratio=TARGET_ELITE_RATIO,
        max_iterations=MAX_ITERATIONS,
        elite_keep_ratio=ELITE_KEEP_RATIO,
        k_group=None,
        psi=PSI,
        selection_cycles=SELECTION_CYCLES,
        mutation_probability=MUTATION_PROBABILITY,
        elite_ratio_plot_thresholds=ELITE_RATIO_PLOT_THRESHOLDS,
        x1_bounds=(st1.X1_L, st1.X1_H),
        x2_bounds=(st1.X2_L, st1.X2_H),
    )

    print("\nСТАДИЯ 4: циклическая эволюция до достижения целевой доли элитных точек")
    print(f"Итоговый размер популяции = {len(final_population)}")
    print(f"Общее число накопленных элитных точек = {len(all_elites)}")
    print(f"Доля прямого переноса лучших особей = {ELITE_KEEP_RATIO * 100:.1f}%")
    print(f"Базовая вероятность мутации = {MUTATION_PROBABILITY:.4f}")
    print(
        f"Адаптивная мутация: старт с доли элитных {ADAPTIVE_MUTATION_START_ELITE_RATIO * 100:.1f}%, "
        f"максимум {ADAPTIVE_MUTATION_MAX_PROBABILITY:.4f}"
    )

    print_stage4_history(history)

    print("\nПервые 30 особей финальной популяции:")
    st1.print_population(final_population, limit=30)
    print_first_elite_points(all_elites, limit=50)

    plot_threshold_populations(
        threshold_snapshots=threshold_snapshots,
        thresholds=ELITE_RATIO_PLOT_THRESHOLDS,
    )

    plot_elite_ratio_dynamics(history)

    all_elite_objs, _, _, all_elite_pareto_idx = st2.rank_population_methodical(
        all_elites,
        psi=PSI,
        x1_bounds=(st1.X1_L, st1.X1_H),
        x2_bounds=(st1.X2_L, st1.X2_H),
    )

    plot_population_with_pareto_front(
        all_elite_objs,
        all_elite_pareto_idx,
        title="Этап 4: все накопленные элитные точки и Парето-оптимальные среди них",
        show_all_label="все накопленные элитные точки",
        show_elite_label="Парето-оптимальные среди накопленных",
    )
