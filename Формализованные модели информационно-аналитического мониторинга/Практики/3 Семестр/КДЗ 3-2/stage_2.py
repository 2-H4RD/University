from __future__ import annotations

from collections import Counter
from typing import Dict, Iterable, List, Sequence, Tuple

import config as cfg
import stage_1 as st1


A_MATRIX = cfg.A_PAYOFF_MATRIX
B_MATRIX = cfg.B_PAYOFF_MATRIX
PSI = cfg.PSI
ARCHIVE_ROUND_DIGITS = cfg.ARCHIVE_ROUND_DIGITS


# ------------------------------------------------------------
# ВЫЧИСЛЕНИЕ ВЫИГРЫШЕЙ В БИМАТРИЧНОЙ ИГРЕ
# ------------------------------------------------------------
def payoff_a(strategy_a: Sequence[float], strategy_b: Sequence[float]) -> float:
    value = 0.0
    for i, p_i in enumerate(strategy_a):
        for j, q_j in enumerate(strategy_b):
            value += p_i * A_MATRIX[i][j] * q_j
    return value



def payoff_b(strategy_a: Sequence[float], strategy_b: Sequence[float]) -> float:
    value = 0.0
    for i, p_i in enumerate(strategy_a):
        for j, q_j in enumerate(strategy_b):
            value += p_i * B_MATRIX[i][j] * q_j
    return value



def decode_and_evaluate(individual: st1.Individual) -> Tuple[List[float], List[float], float, float]:
    strategy_a, strategy_b = st1.decode_individual_to_strategy_profile(individual)
    u_a = payoff_a(strategy_a, strategy_b)
    u_b = payoff_b(strategy_a, strategy_b)
    return strategy_a, strategy_b, u_a, u_b



def build_payoff_pairs(population: Sequence[st1.Individual]) -> List[Tuple[float, float]]:
    pairs: List[Tuple[float, float]] = []
    for individual in population:
        _, _, u_a, u_b = decode_and_evaluate(individual)
        pairs.append((u_a, u_b))
    return pairs


# ------------------------------------------------------------
# СЛУЖЕБНЫЕ ГЕОМЕТРИЧЕСКИЕ ФУНКЦИИ
# ------------------------------------------------------------
def _rounded_point(point: Tuple[float, float], round_digits: int = ARCHIVE_ROUND_DIGITS) -> Tuple[float, float]:
    return (round(float(point[0]), round_digits), round(float(point[1]), round_digits))



def unique_points(
    points: Iterable[Tuple[float, float]],
    round_digits: int = ARCHIVE_ROUND_DIGITS,
) -> List[Tuple[float, float]]:
    unique_map: Dict[Tuple[float, float], Tuple[float, float]] = {}
    for point in points:
        unique_map[_rounded_point(point, round_digits=round_digits)] = (float(point[0]), float(point[1]))
    return list(unique_map.values())



def _cross(o: Tuple[float, float], a: Tuple[float, float], b: Tuple[float, float]) -> float:
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])



def convex_hull(points: Sequence[Tuple[float, float]]) -> List[Tuple[float, float]]:
    pts = sorted(unique_points(points))
    if len(pts) <= 1:
        return pts

    lower: List[Tuple[float, float]] = []
    for point in pts:
        while len(lower) >= 2 and _cross(lower[-2], lower[-1], point) <= 0.0:
            lower.pop()
        lower.append(point)

    upper: List[Tuple[float, float]] = []
    for point in reversed(pts):
        while len(upper) >= 2 and _cross(upper[-2], upper[-1], point) <= 0.0:
            upper.pop()
        upper.append(point)

    hull = lower[:-1] + upper[:-1]
    return hull if hull else pts



def polygon_area(points: Sequence[Tuple[float, float]]) -> float:
    if len(points) < 3:
        return 0.0
    area = 0.0
    for i, point_i in enumerate(points):
        point_j = points[(i + 1) % len(points)]
        area += point_i[0] * point_j[1] - point_j[0] * point_i[1]
    return 0.5 * abs(area)


# ------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ДАННЫЕ ДЛЯ ВИЗУАЛИЗАЦИИ
# ------------------------------------------------------------
def _integer_compositions(total: int, parts: int):
    if parts <= 0:
        return
    if parts == 1:
        yield (total,)
        return
    for value in range(total + 1):
        for tail in _integer_compositions(total - value, parts - 1):
            yield (value,) + tail



def generate_simplex_grid(dim: int, subdivisions: int) -> List[List[float]]:
    if dim <= 0:
        raise ValueError("dim должен быть > 0")
    if subdivisions <= 0:
        raise ValueError("subdivisions должен быть > 0")

    return [
        [part / subdivisions for part in composition]
        for composition in _integer_compositions(subdivisions, dim)
    ]



def get_pure_payoff_points() -> List[dict]:
    points: List[dict] = []
    for i in range(cfg.ROWS_COUNT):
        for j in range(cfg.COLS_COUNT):
            points.append(
                {
                    "row": i,
                    "col": j,
                    "label": f"(A{i + 1}, B{j + 1})",
                    "payoff": (float(A_MATRIX[i][j]), float(B_MATRIX[i][j])),
                }
            )
    return points



def extract_extreme_pure_payoff_points(
    round_digits: int = ARCHIVE_ROUND_DIGITS,
) -> List[dict]:
    pure_points = get_pure_payoff_points()
    hull = convex_hull([point["payoff"] for point in pure_points])
    hull_keys = {_rounded_point(point, round_digits=round_digits) for point in hull}

    extreme_points: List[dict] = []
    seen = set()
    for point in pure_points:
        point_key = _rounded_point(point["payoff"], round_digits=round_digits)
        if point_key in hull_keys and point_key not in seen:
            extreme_points.append(point)
            seen.add(point_key)

    extreme_points.sort(key=lambda item: (item["payoff"][0], item["payoff"][1]))
    return extreme_points



def _row_payoff_points_for_strategy_b(strategy_b: Sequence[float]) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    for i in range(cfg.ROWS_COUNT):
        u_a = 0.0
        u_b = 0.0
        for j, q_j in enumerate(strategy_b):
            u_a += A_MATRIX[i][j] * q_j
            u_b += B_MATRIX[i][j] * q_j
        points.append((u_a, u_b))
    return points



def _column_payoff_points_for_strategy_a(strategy_a: Sequence[float]) -> List[Tuple[float, float]]:
    points: List[Tuple[float, float]] = []
    for j in range(cfg.COLS_COUNT):
        u_a = 0.0
        u_b = 0.0
        for i, p_i in enumerate(strategy_a):
            u_a += p_i * A_MATRIX[i][j]
            u_b += p_i * B_MATRIX[i][j]
        points.append((u_a, u_b))
    return points



def build_attainable_region_polygons(
    subdivisions: int = cfg.ATTAINABLE_REGION_GRID_SUBDIVISIONS,
    round_digits: int = ARCHIVE_ROUND_DIGITS,
) -> List[List[Tuple[float, float]]]:
    polygons: List[List[Tuple[float, float]]] = []

    strategies_b = generate_simplex_grid(cfg.COLS_COUNT, subdivisions)
    for strategy_b in strategies_b:
        hull = convex_hull(_row_payoff_points_for_strategy_b(strategy_b))
        if len(hull) >= 3 and polygon_area(hull) > 1e-12:
            polygons.append([_rounded_point(point, round_digits=round_digits) for point in hull])

    strategies_a = generate_simplex_grid(cfg.ROWS_COUNT, subdivisions)
    for strategy_a in strategies_a:
        hull = convex_hull(_column_payoff_points_for_strategy_a(strategy_a))
        if len(hull) >= 3 and polygon_area(hull) > 1e-12:
            polygons.append([_rounded_point(point, round_digits=round_digits) for point in hull])

    unique_polygons: Dict[Tuple[Tuple[float, float], ...], List[Tuple[float, float]]] = {}
    for polygon in polygons:
        key = tuple(sorted(polygon))
        unique_polygons[key] = polygon

    return list(unique_polygons.values())



def build_attainable_payoff_cloud_grid(
    subdivisions_a: int = 20,
    subdivisions_b: int = 20,
    include_pure_points: bool = True,
    round_digits: int = ARCHIVE_ROUND_DIGITS,
) -> List[Tuple[float, float]]:
    strategies_a = generate_simplex_grid(cfg.ROWS_COUNT, subdivisions_a)
    strategies_b = generate_simplex_grid(cfg.COLS_COUNT, subdivisions_b)

    points: List[Tuple[float, float]] = []
    for strategy_a in strategies_a:
        for strategy_b in strategies_b:
            points.append((payoff_a(strategy_a, strategy_b), payoff_b(strategy_a, strategy_b)))

    if include_pure_points:
        points.extend(point["payoff"] for point in get_pure_payoff_points())

    return unique_points(points, round_digits=round_digits)



def extract_pareto_front(
    points: Sequence[Tuple[float, float]],
    round_digits: int = ARCHIVE_ROUND_DIGITS,
) -> List[Tuple[float, float]]:
    unique = unique_points(points, round_digits=round_digits)
    pareto_front: List[Tuple[float, float]] = []

    for i, point_i in enumerate(unique):
        dominated = False
        for j, point_j in enumerate(unique):
            if i == j:
                continue
            if dominates_max(point_j, point_i):
                dominated = True
                break
        if not dominated:
            pareto_front.append(point_i)

    pareto_front.sort(key=lambda point: (point[0], point[1]))
    return pareto_front


# ------------------------------------------------------------
# ПАРЕТО-ДОМИНИРОВАНИЕ ДЛЯ МАКСИМИЗАЦИИ
# ------------------------------------------------------------
def dominates_max(point_p: Tuple[float, float], point_q: Tuple[float, float]) -> bool:
    return (point_p[0] >= point_q[0] and point_p[1] >= point_q[1]) and (
        point_p[0] > point_q[0] or point_p[1] > point_q[1]
    )


class _FenwickTree:
    def __init__(self, size: int) -> None:
        self.size = size
        self.tree = [0] * (size + 1)

    def add(self, index: int, delta: int) -> None:
        while index <= self.size:
            self.tree[index] += delta
            index += index & -index

    def prefix_sum(self, index: int) -> int:
        result = 0
        while index > 0:
            result += self.tree[index]
            index -= index & -index
        return result



def count_dominators_2d_max(payoff_pairs: Sequence[Tuple[float, float]]) -> List[int]:
    n = len(payoff_pairs)
    if n == 0:
        return []

    unique_y = sorted({pair[1] for pair in payoff_pairs})
    y_to_rank = {value: index + 1 for index, value in enumerate(unique_y)}
    max_rank = len(unique_y)

    indexed_points = list(enumerate(payoff_pairs))
    indexed_points.sort(key=lambda item: (-item[1][0], -item[1][1]))

    fenwick = _FenwickTree(max_rank)
    processed_total = 0
    dominator_counts = [0] * n

    position = 0
    while position < n:
        current_x = indexed_points[position][1][0]
        group_end = position
        while group_end < n and indexed_points[group_end][1][0] == current_x:
            group_end += 1

        group = indexed_points[position:group_end]
        y_counter = Counter(point[1][1] for point in group)
        larger_y_same_x = 0

        for y_value in sorted(y_counter.keys(), reverse=True):
            same_x_same_y_indices = [index for index, point in group if point[1] == y_value]
            rank = y_to_rank[y_value]
            strictly_smaller_y_count = fenwick.prefix_sum(rank - 1)
            previous_with_y_ge = processed_total - strictly_smaller_y_count
            dominators_here = previous_with_y_ge + larger_y_same_x
            for index in same_x_same_y_indices:
                dominator_counts[index] = dominators_here
            larger_y_same_x += y_counter[y_value]

        for _, point in group:
            fenwick.add(y_to_rank[point[1]], 1)
            processed_total += 1

        position = group_end

    return dominator_counts



def phi_from_dominator_counts(dominator_counts: Sequence[int], psi: float = PSI) -> List[float]:
    n = len(dominator_counts)
    if n == 0:
        return []
    if n == 1:
        return [1.0]
    if psi < 0:
        raise ValueError("psi должен быть >= 0")

    denom = n - 1
    phi_list: List[float] = []
    for b_i in dominator_counts:
        base = 1.0 + (b_i / denom)
        phi = 1.0 if psi == 0 else 1.0 / (base ** psi)
        phi_list.append(phi)
    return phi_list



def rank_population_pareto(
    population: Sequence[st1.Individual],
    psi: float = PSI,
) -> Tuple[List[Tuple[float, float]], List[int], List[float], List[int]]:
    payoff_pairs = build_payoff_pairs(population)
    dominator_counts = count_dominators_2d_max(payoff_pairs)
    phi_list = phi_from_dominator_counts(dominator_counts, psi=psi)

    elite_idx: List[int] = []
    for index, dominators in enumerate(dominator_counts):
        if dominators == 0:
            elite_idx.append(index)

    return payoff_pairs, dominator_counts, phi_list, elite_idx


# ------------------------------------------------------------
# АРХИВ ПАРЕТО
# ------------------------------------------------------------
def _archive_key(individual: st1.Individual) -> Tuple[float, ...]:
    strategy_a, strategy_b = st1.decode_individual_to_strategy_profile(individual)
    _, _, u_a, u_b = decode_and_evaluate(individual)
    rounded = tuple(round(value, ARCHIVE_ROUND_DIGITS) for value in (u_a, u_b, *strategy_a, *strategy_b))
    return rounded



def merge_and_prune_pareto_archive(
    archive: Sequence[st1.Individual],
    candidates: Sequence[st1.Individual],
    psi: float = PSI,
) -> List[st1.Individual]:
    merged: List[st1.Individual] = st1.clone_population(archive) + st1.clone_population(candidates)
    if not merged:
        return []

    unique_map = {}
    for individual in merged:
        unique_map[_archive_key(individual)] = individual
    unique_population = list(unique_map.values())

    _, _, _, elite_idx = rank_population_pareto(unique_population, psi=psi)
    return [st1.clone_individual(unique_population[index]) for index in elite_idx]



def sort_population_by_fitness_desc(
    population: Sequence[st1.Individual],
    fitness_list: Sequence[float],
) -> List[st1.Individual]:
    if len(population) != len(fitness_list):
        raise ValueError("Длины population и fitness_list должны совпадать")
    indices = list(range(len(population)))
    indices.sort(key=lambda i: fitness_list[i], reverse=True)
    return [st1.clone_individual(population[i]) for i in indices]
