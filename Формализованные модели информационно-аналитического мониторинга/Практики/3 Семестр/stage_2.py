# stage2_ranking.py
# ЭТАП 2. Ранжирование по методичке и выделение элитных точек (недоминируемых по (f1,f2))
#
# ВАЖНОЕ ИЗМЕНЕНИЕ ПО ЗАПРОСУ:
# - график строится в пространстве критериев (f1, f2), а НЕ (x1, x2)
# - все точки: синие
# - элитные (Φ=1): зелёные
#
# Ранжирование по методичке:
#   Φ(x̃^i) = 1 / ( 1 + b_i/(N-1) )^Ψ
# где:
#   b_i — сколько точек доминируют i в (f1,f2) (минимизация)
#   Ψ — скаляр (для Φ∈[0,1] используйте Ψ>=0)
# Элитные: Φ = 1 (эквивалентно b_i=0 при Ψ>0)

from __future__ import annotations

from typing import List, Tuple
import math
import matplotlib.pyplot as plt

import stage_1 as st1


# =====================================================================
# НАСТРОЙКИ ЭТАПА 2
# =====================================================================
PSI = 2.0  # Ψ из методички (можно любое, для Φ∈[0,1] берите Ψ>=0)
# =====================================================================


# -----------------------------
# Критерии из КДЗ (минимизация)
# -----------------------------
def f1(x1: float, x2: float) -> float:
    return 0.2 * (x1 - 70.0) ** 2 + 0.8 * (x2 - 20.0) ** 2


def f2(x1: float, x2: float) -> float:
    return 0.8 * (x1 - 10.0) ** 2 + 0.2 * (x2 - 70.0) ** 2


# -----------------------------
# Парето-доминация в (f1,f2), минимизация
# -----------------------------
def dominates(p: Tuple[float, float], q: Tuple[float, float]) -> bool:
    return (p[0] <= q[0] and p[1] <= q[1]) and (p[0] < q[0] or p[1] < q[1])


# -----------------------------
# ЭТАП 2: b_i и Φ по формуле методички
# -----------------------------
def rank_population_methodical(
    population: List[st1.Individual],
    psi: float = PSI,
) -> Tuple[List[Tuple[float, float]], List[int], List[float], List[int]]:
    """
    Возвращает:
    - objs: список (f1,f2) для каждой точки
    - b_list: b_i (сколько точек доминируют i) в (f1,f2)
    - phi_list: Φ(x̃^i) = 1 / (1 + b_i/(N-1))^Ψ
    - elite_idx: индексы элитных точек (Φ=1)
    """
    if psi < 0:
        raise ValueError("Для диапазона Φ ∈ [0,1] требуется Ψ >= 0.")

    for ind in population:
        if ind.x1 is None or ind.x2 is None:
            raise RuntimeError("x1/x2 не рассчитаны. Вызовите st1.decode_population_to_grid().")

    # критерии (f1,f2)
    objs: List[Tuple[float, float]] = []
    for ind in population:
        x1v = float(ind.x1)
        x2v = float(ind.x2)
        objs.append((f1(x1v, x2v), f2(x1v, x2v)))

    n = len(population)
    b_list = [0] * n

    # b_i = число доминирующих точек
    for i in range(n):
        cnt = 0
        for j in range(n):
            if i == j:
                continue
            if dominates(objs[j], objs[i]):
                cnt += 1
        b_list[i] = cnt

    # Φ по методичке
    phi_list: List[float] = [1.0] * n
    if n <= 1:
        phi_list[0] = 1.0
    else:
        denom = n - 1
        for i in range(n):
            base = 1.0 + (b_list[i] / denom)  # base ∈ [1,2]
            phi_list[i] = 1.0 / (base ** psi) if psi != 0 else 1.0

    # элитные: Φ=1 (с допуском)
    elite_idx = [i for i in range(n) if math.isclose(phi_list[i], 1.0, rel_tol=0.0, abs_tol=1e-12)]
    return objs, b_list, phi_list, elite_idx


# -----------------------------
# График ЭТАП 2: в пространстве критериев (f1,f2)
# -----------------------------
def plot_in_objective_space(
    objs: List[Tuple[float, float]],
    elite_idx: List[int],
    title: str = "ЭТАП 2: популяция (синие) и элитные (зелёные) в пространстве критериев (f1,f2)",
) -> None:
    all_f1 = [p[0] for p in objs]
    all_f2 = [p[1] for p in objs]

    elite_f1 = [objs[i][0] for i in elite_idx]
    elite_f2 = [objs[i][1] for i in elite_idx]

    plt.figure(figsize=(10, 8))

    # Сетка как на первом графике здесь не имеет смысла (f1,f2 не дискретная равномерная сетка),
    # поэтому рисуем обычную координатную сетку.
    plt.grid(True)

    plt.scatter(all_f1, all_f2, s=18, alpha=0.9, c="royalblue", label="вся популяция")
    plt.scatter(
        elite_f1, elite_f2,
        s=30, alpha=1.0, c="limegreen",
        edgecolors="black", linewidths=0.35,
        label="элитные (Φ=1)"
    )

    plt.title(f"{title}\n(N={len(objs)}, elite={len(elite_idx)})")
    plt.xlabel("f1 (min)")
    plt.ylabel("f2 (min)")
    plt.legend()
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # 1) Этап 1: получить начальную популяцию
    pop = st1.generate_initial_population_stratified(
        pop_size=st1.POP_SIZE,
        bits_per_var=st1.BITS_PER_VAR,
        seed=st1.SEED,
    )

    # 2) Этап 1: декодировать x1,x2
    st1.decode_population_to_grid(pop, x1_bounds=(st1.X1_L, st1.X1_H), x2_bounds=(st1.X2_L, st1.X2_H))

    # 3) Этап 2: ранжирование + элита
    objs, b_list, phi_list, elite_idx = rank_population_methodical(pop, psi=PSI)

    print("\nЭТАП 2 (методичка):")
    print(f"N={len(pop)}, Ψ={PSI}")
    print(f"Φ ∈ [{min(phi_list):.6f}, {max(phi_list):.6f}]")
    print(f"Элитных (Φ=1) = {len(elite_idx)}")

    # 4) Этап 2: график в пространстве критериев (f1,f2)
    plot_in_objective_space(objs, elite_idx)