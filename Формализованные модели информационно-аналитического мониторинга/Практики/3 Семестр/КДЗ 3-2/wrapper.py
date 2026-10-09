from __future__ import annotations

from typing import Dict, List, Tuple

import config as cfg
import stage_1 as st1
import stage_2 as st2
import stage_4 as st4


DEFAULT_FIGURE_SIZE = getattr(cfg, "PLOT_FIGURE_SIZE", (11, 8))
DEFAULT_SHOW_PLOT_WINDOW = getattr(cfg, "SHOW_PLOT_WINDOW", True)
DEFAULT_REGION_SUBDIVISIONS = getattr(cfg, "ATTAINABLE_REGION_GRID_SUBDIVISIONS", 40)
DEFAULT_REGION_ALPHA = getattr(cfg, "ATTAINABLE_REGION_ALPHA", 0.10)


# ------------------------------------------------------------
# ОБЁРТКА ДЛЯ РЕШЕНИЯ ПЕРВОГО ЗАДАНИЯ
# ------------------------------------------------------------
def solve_pareto_problem() -> Dict[str, object]:
    st4.initialize_random_seed()
    return st4.run_pareto_ga()


# ------------------------------------------------------------
# ПОДГОТОВКА ДАННЫХ ДЛЯ ГРАФИКА
# ------------------------------------------------------------
def build_visualization_data(
    pareto_result: Dict[str, object],
    region_subdivisions: int = DEFAULT_REGION_SUBDIVISIONS,
) -> Dict[str, object]:
    attainable_region_polygons = st2.build_attainable_region_polygons(subdivisions=region_subdivisions)
    extreme_points = st2.extract_extreme_pure_payoff_points()
    pareto_payoffs = st2.extract_pareto_front(pareto_result["pareto_payoffs"])

    axis_points: List[Tuple[float, float]] = []
    for polygon in attainable_region_polygons:
        axis_points.extend(polygon)
    axis_points.extend(point["payoff"] for point in extreme_points)
    axis_points.extend(pareto_payoffs)

    return {
        "attainable_region_polygons": attainable_region_polygons,
        "extreme_points": extreme_points,
        "pareto_payoffs": pareto_payoffs,
        "axis_points": axis_points,
    }


# ------------------------------------------------------------
# ПОСТРОЕНИЕ ГРАФИКА ПЕРВОГО ЗАДАНИЯ
# ------------------------------------------------------------
def plot_task1_pareto_summary(
    plot_data: Dict[str, object],
    show_window: bool = DEFAULT_SHOW_PLOT_WINDOW,
) -> None:
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection

    attainable_region_polygons: List[List[Tuple[float, float]]] = plot_data["attainable_region_polygons"]
    extreme_points = plot_data["extreme_points"]
    pareto_payoffs: List[Tuple[float, float]] = plot_data["pareto_payoffs"]
    axis_points: List[Tuple[float, float]] = plot_data["axis_points"]

    fig, ax = plt.subplots(figsize=DEFAULT_FIGURE_SIZE)

    if attainable_region_polygons:
        collection = PolyCollection(
            attainable_region_polygons,
            facecolors="tab:blue",
            edgecolors="none",
            alpha=DEFAULT_REGION_ALPHA,
            label="Множество достижимых выплат",
            zorder=1,
        )
        ax.add_collection(collection)

    if pareto_payoffs:
        pareto_payoffs = sorted(pareto_payoffs, key=lambda point: (point[0], point[1]))
        pareto_x = [point[0] for point in pareto_payoffs]
        pareto_y = [point[1] for point in pareto_payoffs]
        ax.scatter(
            pareto_x,
            pareto_y,
            s=getattr(cfg, "PARETO_MARKER_SIZE", 28),
            color="green",
            label="Парето-оптимальные точки",
            zorder=3,
        )
        ax.plot(
            pareto_x,
            pareto_y,
            color="green",
            linewidth=1.4,
            alpha=0.65,
            zorder=2,
        )

    if extreme_points:
        extreme_x = [point["payoff"][0] for point in extreme_points]
        extreme_y = [point["payoff"][1] for point in extreme_points]
        ax.scatter(
            extreme_x,
            extreme_y,
            s=getattr(cfg, "EXTREME_MARKER_SIZE", 90),
            marker="D",
            color="black",
            label="Крайние точки",
            zorder=4,
        )
        for point in extreme_points:
            x, y = point["payoff"]
            ax.annotate(
                point["label"],
                xy=(x, y),
                xytext=(8, 8),
                textcoords="offset points",
                fontsize=11,
                color="black",
                zorder=5,
            )

    ax.set_title(getattr(cfg, "PLOT_TITLE", "Множество достижимых выплат и Парето-оптимальные решения"), fontsize=16)
    ax.set_xlabel(getattr(cfg, "PLOT_X_LABEL", r"$u_A(p, q)$ — выигрыш игрока A"), fontsize=13)
    ax.set_ylabel(getattr(cfg, "PLOT_Y_LABEL", r"$u_B(p, q)$ — выигрыш игрока B"), fontsize=13)
    ax.grid(True, alpha=0.45)
    ax.legend(loc="best", fontsize=11)

    if axis_points:
        all_x = [point[0] for point in axis_points]
        all_y = [point[1] for point in axis_points]
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        pad_x = max(0.15, 0.06 * (max_x - min_x if max_x > min_x else 1.0))
        pad_y = max(0.15, 0.06 * (max_y - min_y if max_y > min_y else 1.0))
        ax.set_xlim(min_x - pad_x, max_x + pad_x)
        ax.set_ylim(min_y - pad_y, max_y + pad_y)

    fig.tight_layout()

    try:
        if show_window:
            plt.show()
    finally:
        plt.close(fig)


# ------------------------------------------------------------
# ТЕКСТОВЫЙ ВЫВОД
# ------------------------------------------------------------
def _print_pareto_block(result: Dict[str, object]) -> None:
    archive = result["pareto_archive"]
    payoffs = result["pareto_payoffs"]
    strategies = result["pareto_strategies"]

    print()
    print("1) МНОЖЕСТВО ПАРЕТО-ОПТИМАЛЬНЫХ РЕШЕНИЙ")
    print(f"   Число решений в архиве: {len(archive)}")

    preview_count = min(10, len(archive))
    for i in range(preview_count):
        strategy_a, strategy_b = strategies[i]
        u_a, u_b = payoffs[i]
        print(f"   Решение #{i + 1}")
        print(f"     p = {st1.format_probability_vector(strategy_a)}")
        print(f"     q = {st1.format_probability_vector(strategy_b)}")
        print(f"     (u_A, u_B) = ({u_a:.6f}, {u_b:.6f})")


if __name__ == "__main__":
    pareto_result = solve_pareto_problem()
    plot_data = build_visualization_data(pareto_result)
    _print_pareto_block(pareto_result)
    plot_task1_pareto_summary(plot_data)
