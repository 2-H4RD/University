# stage1_population.py
# ЭТАП 1 (Variant B, масштабируемый). Генерация начальной популяции со стратификацией,
# БЕЗ построения списка 0..2^m-1 (что невозможно при m=32).
#
# Стратификация (LHS по индексам l):
# - делим [0,1) на POP_SIZE равных интервалов (strata)
# - из каждого интервала берём случайную точку u
# - переводим u в индекс уровня l = floor(u * 2^m)
# - для второй координаты используем перестановку интервалов
# - l -> Gray(l) -> генотип (список бит 0/1)
#
# Модульность:
# - generate_initial_population_stratified() можно импортировать в общий ГА
# - decode_population_to_grid() декодирует x1,x2
# - compute_grid_for_plot()/extract_xy() удобно использовать в ЭТАП 2 для аналогичного графика

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import random


# =====================================================================
# ЕДИНЫЙ БЛОК НАСТРОЕК (меняете только здесь)
# =====================================================================
SEED = 42
POP_SIZE = 10000
BITS_PER_VAR = 32

X1_L, X1_H = 0.0, 79.0
X2_L, X2_H = 0.0, 79.0

LEVELS = 2 ** BITS_PER_VAR
MAX_L = LEVELS - 1
STEP = (X1_H - X1_L) / MAX_L

DRAW_FULL_GRID_IF_LEVELS_LEQ = 64
# =====================================================================


@dataclass
class Individual:
    genotype: List[int]
    bits_per_var: int = BITS_PER_VAR

    # заполняется при генерации/декодировании (для теста/визуализации)
    l1: Optional[int] = None
    l2: Optional[int] = None
    x1: Optional[float] = None
    x2: Optional[float] = None

    @property
    def gray_x1(self) -> List[int]:
        return self.genotype[: self.bits_per_var]

    @property
    def gray_x2(self) -> List[int]:
        return self.genotype[self.bits_per_var :]


# -----------------------------
# Служебное: l -> Gray bits (без format)
# -----------------------------
def _int_to_gray_bits(l: int, m: int) -> List[int]:
    """
    l -> Gray(l)=l^(l>>1) -> m бит (список 0/1), старший бит первым.
    """
    g = l ^ (l >> 1)
    return [(g >> shift) & 1 for shift in range(m - 1, -1, -1)]


# -----------------------------
# Служебное: Gray bits -> int (быстро, целочисленно)
# -----------------------------
def _gray_bits_to_int(gray_bits: List[int]) -> int:
    """
    Gray-биты -> целое l:
    1) bits -> gray_int
    2) gray_int -> binary_int через: b ^= (g>>1); g>>=1
    """
    gray_int = 0
    for bit in gray_bits:
        gray_int = (gray_int << 1) | bit

    b = gray_int
    t = gray_int >> 1
    while t:
        b ^= t
        t >>= 1
    return b


# -----------------------------
# Генератор (Variant B): LHS-стратификация без range(2^m)
# -----------------------------
def generate_initial_population_stratified(
    pop_size: int = POP_SIZE,
    bits_per_var: int = BITS_PER_VAR,
    seed: Optional[int] = SEED,
) -> List[Individual]:
    """
    Стратифицированная генерация по индексам l1,l2 без построения 0..2^m-1.

    Сложность: O(pop_size * bits_per_var)
    Память: O(pop_size)
    """
    if pop_size <= 0:
        raise ValueError("pop_size должен быть > 0")
    if bits_per_var <= 0:
        raise ValueError("bits_per_var должен быть > 0")

    if seed is not None:
        random.seed(seed)

    levels = 1 << bits_per_var
    max_l = levels - 1

    # Перестановка страт для второй координаты (аналог LHS)
    strata_perm = list(range(pop_size))
    random.shuffle(strata_perm)

    population: List[Individual] = []

    for k in range(pop_size):
        u1 = (k + random.random()) / pop_size
        u2 = (strata_perm[k] + random.random()) / pop_size

        l1 = int(u1 * levels)
        l2 = int(u2 * levels)

        # защита от редкого случая выхода за границу из-за float
        if l1 > max_l:
            l1 = max_l
        if l2 > max_l:
            l2 = max_l

        gray1 = _int_to_gray_bits(l1, bits_per_var)
        gray2 = _int_to_gray_bits(l2, bits_per_var)
        genotype = gray1 + gray2

        population.append(Individual(genotype=genotype, bits_per_var=bits_per_var, l1=l1, l2=l2))

    return population


# -----------------------------
# Декодирование l->x (для теста/визуализации и Stage 2)
# -----------------------------
def decode_population_to_grid(
    population: List[Individual],
    x1_bounds: Tuple[float, float] = (X1_L, X1_H),
    x2_bounds: Tuple[float, float] = (X2_L, X2_H),
) -> None:
    if not population:
        return

    m = population[0].bits_per_var
    max_l = (1 << m) - 1

    x1_Lc, x1_Hc = x1_bounds
    x2_Lc, x2_Hc = x2_bounds

    for ind in population:
        # если l1/l2 уже заданы генератором — используем их
        if ind.l1 is None:
            ind.l1 = _gray_bits_to_int(ind.gray_x1)
        if ind.l2 is None:
            ind.l2 = _gray_bits_to_int(ind.gray_x2)

        l1 = int(ind.l1)
        l2 = int(ind.l2)

        ind.x1 = x1_Lc + l1 * (x1_Hc - x1_Lc) / max_l
        ind.x2 = x2_Lc + l2 * (x2_Hc - x2_Lc) / max_l


# -----------------------------
# Утилиты для Stage 2 (аналогичный график)
# -----------------------------
def extract_xy(population: List[Individual]) -> Tuple[List[float], List[float]]:
    """
    Возвращает (pop_x, pop_y) строго как List[float] (без Optional) — удобно для matplotlib/Pylance.
    Требует, чтобы x1/x2 уже были рассчитаны.
    """
    pop_x: List[float] = []
    pop_y: List[float] = []
    for ind in population:
        if ind.x1 is None or ind.x2 is None:
            raise RuntimeError("x1/x2 не рассчитаны. Сначала вызовите decode_population_to_grid().")
        pop_x.append(float(ind.x1))
        pop_y.append(float(ind.x2))
    return pop_x, pop_y


def compute_grid_for_plot(
    bits_per_var: int,
    x1_bounds: Tuple[float, float],
    x2_bounds: Tuple[float, float],
    draw_full_grid_if_levels_leq: int = DRAW_FULL_GRID_IF_LEVELS_LEQ,
) -> Dict[str, object]:
    """
    Возвращает данные для "такой же сетки как в этапе 1":
    - levels (список уровней) — только если уровней <= порога
    - grid_x, grid_y — узлы сетки (для scatter) — только если уровней <= порога
    - step_x — шаг по оси (для padding)
    """
    m = bits_per_var
    levels_count = 1 << m
    max_l = levels_count - 1

    x1_Lc, x1_Hc = x1_bounds
    x2_Lc, x2_Hc = x2_bounds

    step_x = (x1_Hc - x1_Lc) / max_l if max_l != 0 else 1.0

    levels: List[float] = []
    grid_x: List[float] = []
    grid_y: List[float] = []

    if levels_count <= draw_full_grid_if_levels_leq and max_l != 0:
        levels = [x1_Lc + l * (x1_Hc - x1_Lc) / max_l for l in range(max_l + 1)]
        for xv in levels:
            for yv in levels:
                grid_x.append(xv)
                grid_y.append(yv)

    return {
        "levels": levels,
        "grid_x": grid_x,
        "grid_y": grid_y,
        "step_x": step_x,
        "levels_count": levels_count,
    }


# -----------------------------
# Визуализация этапа 1 (опционально)
# -----------------------------
def plot_population_on_grid(
    population: List[Individual],
    x1_bounds: Tuple[float, float] = (X1_L, X1_H),
    x2_bounds: Tuple[float, float] = (X2_L, X2_H),
    title: str = "ЭТАП 1 (Variant B): начальная популяция на сетке",
) -> None:
    import matplotlib.pyplot as plt

    if not population:
        raise ValueError("Популяция пуста")

    if population[0].x1 is None or population[0].x2 is None:
        decode_population_to_grid(population, x1_bounds=x1_bounds, x2_bounds=x2_bounds)

    grid = compute_grid_for_plot(population[0].bits_per_var, x1_bounds, x2_bounds)
    levels = grid["levels"]
    grid_x = grid["grid_x"]
    grid_y = grid["grid_y"]
    step_x = float(grid["step_x"])

    pop_x, pop_y = extract_xy(population)

    plt.figure(figsize=(10, 8))

    if grid_x:
        plt.scatter(grid_x, grid_y, alpha=0.15, label="узлы сетки (дискретизация)")

    plt.scatter(pop_x, pop_y, s=20, alpha=1.0, label="начальная популяция")

    m = population[0].bits_per_var
    plt.title(f"{title} (m={m}, N={len(population)})")
    plt.xlabel("x1")
    plt.ylabel("x2")

    if levels:
        plt.xticks(levels, rotation=90 if len(levels) > 16 else 0)
        plt.yticks(levels)

    x1_Lc, x1_Hc = x1_bounds
    x2_Lc, x2_Hc = x2_bounds
    plt.grid(True)
    plt.xlim(x1_Lc - 0.5 * step_x, x1_Hc + 0.5 * step_x)
    plt.ylim(x2_Lc - 0.5 * step_x, x2_Hc + 0.5 * step_x)

    plt.legend()
    plt.tight_layout()
    plt.show()


# -----------------------------
# Тестовый вывод таблицы генотипов
# -----------------------------
def _format_bits(bits: List[int]) -> str:
    return "".join(str(b) for b in bits)


def _print_population(population: List[Individual], limit: int = 30) -> None:
    rows = []
    for i, ind in enumerate(population[:limit], start=1):
        rows.append({
            "#": i,
            "genotype Gray (x1|x2)": f"{_format_bits(ind.gray_x1)}|{_format_bits(ind.gray_x2)}",
            "l1": ind.l1,
            "l2": ind.l2,
        })

    try:
        from tabulate import tabulate
        print(tabulate(rows, headers="keys", tablefmt="grid", showindex=False))
    except Exception:
        print(" # | genotype Gray (x1|x2) | l1 l2")
        print("-" * 40)
        for r in rows:
            print(f"{r['#']:2d} | {r['genotype Gray (x1|x2)']} | {r['l1']} {r['l2']}")


if __name__ == "__main__":
    pop = generate_initial_population_stratified(
        pop_size=POP_SIZE, bits_per_var=BITS_PER_VAR, seed=SEED
    )

    decode_population_to_grid(pop, x1_bounds=(X1_L, X1_H), x2_bounds=(X2_L, X2_H))

    print(
        f"\nЭТАП 1 (Variant B, LHS): стратифицированная популяция "
        f"(SEED={SEED}, POP_SIZE={POP_SIZE}, BITS_PER_VAR={BITS_PER_VAR}, LEVELS=2^{BITS_PER_VAR}, STEP≈{STEP:.6e})"
    )
    _print_population(pop, limit=30)

    plot_population_on_grid(pop, x1_bounds=(X1_L, X1_H), x2_bounds=(X2_L, X2_H))