from __future__ import annotations

from typing import List, Tuple
import math
import matplotlib.pyplot as plt

import config as cfg
import stage_1 as st1


# =====================================================================
# НАСТРОЙКИ ЭТАПА 2
# =====================================================================
PSI = cfg.PSI
# =====================================================================


# ------------------------------------------------------------
# КРИТЕРИИ (минимизация)
# ------------------------------------------------------------
def f1(x1: float, x2: float) -> float:
    return 0.2 * (x1 - 70.0) ** 2 + 0.8 * (x2 - 20.0) ** 2


def f2(x1: float, x2: float) -> float:
    return 0.8 * (x1 - 10.0) ** 2 + 0.2 * (x2 - 70.0) ** 2


# ------------------------------------------------------------
# ПАРЕТО-ДОМИНИРОВАНИЕ В (f1, f2), МИНИМИЗАЦИЯ
# ------------------------------------------------------------
def dominates(p: Tuple[float, float], q: Tuple[float, float]) -> bool:
    return (p[0] <= q[0] and p[1] <= q[1]) and (p[0] < q[0] or p[1] < q[1])

class FenwickTree:
    """
    Дерево Фенвика для подсчёта числа уже обработанных точек
    с рангом f2 <= заданного.
    """
    def __init__(self, size: int):
        if size <= 0:
            raise ValueError("size должен быть > 0")
        self.size = size
        self.tree = [0] * (size + 1)

    def update(self, index: int, delta: int) -> None:
        while index <= self.size:
            self.tree[index] += delta
            index += index & -index

    def query(self, index: int) -> int:
        result = 0
        while index > 0:
            result += self.tree[index]
            index -= index & -index
        return result


def count_dominators_2d(
    objs: List[Tuple[float, float]],
) -> List[int]:
    """
    Считает для каждой точки число доминирующих её точек в задаче
    двухкритериальной минимизации.

    Алгоритм эквивалентен полному попарному перебору, но работает
    за O(N log N) за счёт сортировки по f1 и дерева Фенвика по f2.

    Важный момент: точки с одинаковыми (f1, f2) не доминируют друг друга.
    """
    n = len(objs)
    if n == 0:
        return []

    unique_f2 = sorted({f2_value for _, f2_value in objs})
    f2_rank = {value: rank + 1 for rank, value in enumerate(unique_f2)}

    points = []
    for index, (f1_value, f2_value) in enumerate(objs):
        points.append((f1_value, f2_value, index, f2_rank[f2_value]))

    points.sort(key=lambda point: (point[0], point[1]))

    bit = FenwickTree(len(unique_f2))
    b_list = [0] * n

    i = 0
    while i < n:
        j = i
        current_f1 = points[i][0]

        while j < n and points[j][0] == current_f1:
            j += 1

        # Вклад от точек с меньшим f1 (они уже добавлены в Fenwick tree).
        prev_counts = {}
        for k in range(i, j):
            _, _, original_index, rank_f2 = points[k]
            prev_counts[original_index] = bit.query(rank_f2)

        # Вклад внутри блока одинакового f1: доминируют только точки
        # с тем же f1, но строго меньшим f2.
        less_in_block = 0
        t = i
        while t < j:
            u = t
            current_f2 = points[t][1]

            while u < j and points[u][1] == current_f2:
                u += 1

            for k in range(t, u):
                _, _, original_index, _ = points[k]
                b_list[original_index] = prev_counts[original_index] + less_in_block

            less_in_block += (u - t)
            t = u

        for k in range(i, j):
            _, _, _, rank_f2 = points[k]
            bit.update(rank_f2, 1)

        i = j

    return b_list



# ------------------------------------------------------------
# ДЕКОДИРОВАНИЕ ПОПУЛЯЦИИ В ПРОСТРАНСТВО КРИТЕРИЕВ
# ------------------------------------------------------------
def build_objectives(
    population: List[st1.Individual],
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> List[Tuple[float, float]]:
    objs: List[Tuple[float, float]] = []

    for ind in population:
        x1_value, x2_value = st1.decode_individual_to_xy(
            ind,
            x1_bounds=x1_bounds,
            x2_bounds=x2_bounds,
        )
        objs.append((f1(x1_value, x2_value), f2(x1_value, x2_value)))

    return objs


# ------------------------------------------------------------
# ЭТАП 2: b_i И Phi ПО ФОРМУЛЕ МЕТОДИЧКИ
# ------------------------------------------------------------
def rank_population_methodical(
    population: List[st1.Individual],
    psi: float = PSI,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> Tuple[List[Tuple[float, float]], List[int], List[float], List[int]]:
    """
    Возвращает:
    - objs: список (f1, f2) для каждой особи
    - b_list: b_i = сколько точек доминируют i
    - phi_list: Phi(x_i) = 1 / (1 + b_i / (N - 1))^psi
    - elite_idx: индексы элитных точек (Phi = 1)
    """
    if psi < 0:
        raise ValueError("Для диапазона Phi ∈ [0, 1] требуется psi >= 0.")

    n = len(population)
    if n == 0:
        return [], [], [], []

    objs = build_objectives(
        population,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )

    b_list = count_dominators_2d(objs)

    phi_list: List[float] = [1.0] * n

    if n == 1:
        phi_list[0] = 1.0
    else:
        denom = n - 1
        for i in range(n):
            base = 1.0 + (b_list[i] / denom)
            if psi == 0:
                phi_list[i] = 1.0
            else:
                phi_list[i] = 1.0 / (base ** psi)

    elite_idx = []
    for i in range(n):
        if math.isclose(phi_list[i], 1.0, rel_tol=0.0, abs_tol=1e-12):
            elite_idx.append(i)

    return objs, b_list, phi_list, elite_idx


# ------------------------------------------------------------
# ТАБЛИЦА ДЛЯ КОНСОЛИ
# ------------------------------------------------------------
def print_stage2_table(
    population: List[st1.Individual],
    objs: List[Tuple[float, float]],
    b_list: List[int],
    phi_list: List[float],
    limit: int = 30,
) -> None:
    rows = []

    count = min(limit, len(population))
    for i in range(count):
        ind = population[i]
        rows.append({
            "#": i + 1,
            "Gray x1": st1.bits_to_string(ind.gray_x1),
            "Gray x2": st1.bits_to_string(ind.gray_x2),
            "Генотип": st1.bits_to_string(ind.genotype),
            "f1": f"{objs[i][0]:.6f}",
            "f2": f"{objs[i][1]:.6f}",
            "b_i": b_list[i],
            "Phi": f"{phi_list[i]:.6f}",
        })

    try:
        from tabulate import tabulate
        print(tabulate(rows, headers="keys", tablefmt="grid", showindex=False))
    except Exception:
        print("# | Gray x1 | Gray x2 | Генотип | f1 | f2 | b_i | Phi")
        print("-" * 160)
        for row in rows:
            print(
                f"{row['#']} | {row['Gray x1']} | {row['Gray x2']} | "
                f"{row['Генотип']} | {row['f1']} | {row['f2']} | "
                f"{row['b_i']} | {row['Phi']}"
            )


# ------------------------------------------------------------
# ГРАФИК В ПРОСТРАНСТВЕ КРИТЕРИЕВ (f1, f2)
# ------------------------------------------------------------
def plot_in_objective_space(
    objs: List[Tuple[float, float]],
    elite_idx: List[int],
    title: str = "ЭТАП 2: популяция и элитные точки в пространстве критериев (f1, f2)",
) -> None:
    if not objs:
        raise ValueError("Список критериев пуст")

    all_f1 = [point[0] for point in objs]
    all_f2 = [point[1] for point in objs]

    elite_f1 = [objs[i][0] for i in elite_idx]
    elite_f2 = [objs[i][1] for i in elite_idx]

    plt.figure(figsize=(10, 8))
    plt.grid(True)

    plt.scatter(all_f1, all_f2, s=18, alpha=0.9, label="вся популяция")
    plt.scatter(
        elite_f1,
        elite_f2,
        s=30,
        alpha=1.0,
        edgecolors="black",
        linewidths=0.35,
        label="элитные (Phi = 1)",
    )

    plt.title(f"{title}\n(N={len(objs)}, elite={len(elite_idx)})")
    plt.xlabel("f1 (min)")
    plt.ylabel("f2 (min)")
    plt.legend()
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------
if __name__ == "__main__":
    # 1) Этап 1: получить начальную популяцию
    population = st1.generate_initial_population(
        pop_size=st1.POP_SIZE,
        bits_per_var=st1.BITS_PER_VAR,
    )

    print(
        f"\nЭТАП 1: случайная побитовая генерация начальной популяции "
        f"(POP_SIZE={st1.POP_SIZE}, BITS_PER_VAR={st1.BITS_PER_VAR})"
    )

    st1.print_population(population, limit=30)

    # 2) График этапа 1 в пространстве решений (x1, x2)
    st1.plot_population(
        population,
        x1_bounds=(st1.X1_L, st1.X1_H),
        x2_bounds=(st1.X2_L, st1.X2_H),
        title="ЭТАП 1: начальная популяция в пространстве решений (x1, x2)",
    )

    # 3) Этап 2: ранжирование + элитные точки
    objs, b_list, phi_list, elite_idx = rank_population_methodical(
        population,
        psi=PSI,
        x1_bounds=(st1.X1_L, st1.X1_H),
        x2_bounds=(st1.X2_L, st1.X2_H),
    )

    print("\nЭТАП 2: ранжирование по методичке")
    print(f"N = {len(population)}")
    print(f"PSI = {PSI}")
    print(f"Phi ∈ [{min(phi_list):.6f}, {max(phi_list):.6f}]")
    print(f"Элитных точек (Phi = 1): {len(elite_idx)}")

    print_stage2_table(
        population,
        objs,
        b_list,
        phi_list,
        limit=30,
    )

    # 4) График этапа 2 в пространстве критериев (f1, f2)
    plot_in_objective_space(
        objs,
        elite_idx,
        title="ЭТАП 2: популяция и элитные точки в пространстве критериев (f1, f2)",
    )