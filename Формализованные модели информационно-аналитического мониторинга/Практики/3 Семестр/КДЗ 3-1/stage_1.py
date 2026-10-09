from dataclasses import dataclass
from typing import List, Tuple
import random
import matplotlib.pyplot as plt
from tabulate import tabulate

import config as cfg


# ============================================================
# НАСТРОЙКИ
# ============================================================
POP_SIZE = cfg.POP_SIZE
BITS_PER_VAR = cfg.BITS_PER_VAR

X1_L, X1_H = cfg.X1_L, cfg.X1_H
X2_L, X2_H = cfg.X2_L, cfg.X2_H

DRAW_FULL_GRID_IF_LEVELS_LEQ = cfg.DRAW_FULL_GRID_IF_LEVELS_LEQ
# ============================================================


@dataclass
class Individual:
    genotype: List[int]
    bits_per_var: int

    @property
    def gray_x1(self) -> List[int]:
        return self.genotype[:self.bits_per_var]

    @property
    def gray_x2(self) -> List[int]:
        return self.genotype[self.bits_per_var:]


# ------------------------------------------------------------
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ------------------------------------------------------------
def random_bits(count: int) -> List[int]:
    """Случайно генерирует count битов: 0 или 1."""
    bits = []
    for _ in range(count):
        bits.append(random.randint(0, 1))
    return bits

def int_to_gray_int(value: int) -> int:
    """Переводит обычное целое число в целое число в коде Грея."""
    return value ^ (value >> 1)


def int_to_bits(value: int, bits_count: int) -> List[int]:
    """Преобразует целое число в список битов фиксированной длины."""
    bits = []
    for shift in range(bits_count - 1, -1, -1):
        bits.append((value >> shift) & 1)
    return bits


def gray_int_to_bits(gray_value: int, bits_count: int) -> List[int]:
    """Преобразует целое значение Gray-кода в список битов."""
    return int_to_bits(gray_value, bits_count)


def sample_unique_levels_stratified(
    sample_size: int,
    levels_per_axis: int,
) -> List[int]:
    """
    Выбирает sample_size уникальных уровней так, чтобы проекция на ось
    была равномерной и при этом оставалась случайной.

    Диапазон уровней [0, levels_per_axis) делится на sample_size
    непересекающихся страт. Из каждой страты выбирается ровно один
    случайный уровень, после чего выбранные уровни перемешиваются.
    """
    if sample_size <= 0:
        raise ValueError("sample_size должен быть > 0")
    if levels_per_axis <= 0:
        raise ValueError("levels_per_axis должен быть > 0")
    if sample_size > levels_per_axis:
        raise ValueError(
            "Число выбираемых уровней не может превышать число доступных уровней."
        )

    sampled_levels = []

    for stratum_index in range(sample_size):
        left = (stratum_index * levels_per_axis) // sample_size
        right = ((stratum_index + 1) * levels_per_axis) // sample_size - 1

        if right < left:
            right = left

        sampled_levels.append(random.randint(left, right))

    random.shuffle(sampled_levels)
    return sampled_levels


def gray_bits_to_int(gray_bits: List[int]) -> int:
    """
    Переводит список битов кода Грея в целое число.
    """
    gray_value = 0
    for bit in gray_bits:
        gray_value = (gray_value << 1) | bit

    binary_value = gray_value
    shift_value = gray_value >> 1

    while shift_value > 0:
        binary_value ^= shift_value
        shift_value >>= 1

    return binary_value


def level_to_real(level: int, bits_per_var: int, bounds: Tuple[float, float]) -> float:
    """
    Переводит дискретный уровень в вещественное значение.
    """
    low, high = bounds
    max_level = (1 << bits_per_var) - 1

    if max_level == 0:
        return low

    return low + level * (high - low) / max_level


def decode_individual_to_xy(
    individual: Individual,
    x1_bounds: Tuple[float, float] = (X1_L, X1_H),
    x2_bounds: Tuple[float, float] = (X2_L, X2_H),
) -> Tuple[float, float]:
    """
    Локально декодирует особь в вещественные x1 и x2.
    Значения не сохраняются внутри объекта.
    """
    l1 = gray_bits_to_int(individual.gray_x1)
    l2 = gray_bits_to_int(individual.gray_x2)

    x1 = level_to_real(l1, individual.bits_per_var, x1_bounds)
    x2 = level_to_real(l2, individual.bits_per_var, x2_bounds)

    return x1, x2


# ------------------------------------------------------------
# ГЕНЕРАЦИЯ НАЧАЛЬНОЙ ПОПУЛЯЦИИ
# ------------------------------------------------------------
def generate_initial_population(
    pop_size: int = POP_SIZE,
    bits_per_var: int = BITS_PER_VAR,
) -> List[Individual]:
    """
    Формирует случайную начальную популяцию с равномерными проекциями
    на оси параметров.

    Подход близок к Latin hypercube sampling в пространстве уровней:
    1. По каждой оси диапазон уровней делится на pop_size страт.
    2. Из каждой страты по x1 выбирается один случайный уровень.
    3. Из каждой страты по x2 выбирается один случайный уровень.
    4. Выбранные уровни по x1 и x2 независимо перемешиваются.
    5. После этого они случайно попарно сочетаются в pop_size особей.

    В результате:
    - популяция остаётся случайной;
    - проекции на x1 и x2 распределены равномерно;
    - уровни на каждой оси не повторяются;
    - нет необходимости в отбраковке дубликатов пар в цикле.
    """
    if pop_size <= 0:
        raise ValueError("pop_size должен быть > 0")
    if bits_per_var <= 0:
        raise ValueError("bits_per_var должен быть > 0")

    levels_per_axis = 1 << bits_per_var

    if pop_size > levels_per_axis:
        raise ValueError(
            f"Нельзя создать {pop_size} точек без повторов проекций: "
            f"для bits_per_var={bits_per_var} доступно только {levels_per_axis} уровней на ось"
        )

    levels_x1 = sample_unique_levels_stratified(
        sample_size=pop_size,
        levels_per_axis=levels_per_axis,
    )
    levels_x2 = sample_unique_levels_stratified(
        sample_size=pop_size,
        levels_per_axis=levels_per_axis,
    )

    random.shuffle(levels_x1)
    random.shuffle(levels_x2)

    population = []

    for level_x1, level_x2 in zip(levels_x1, levels_x2):
        gray_x1 = gray_int_to_bits(int_to_gray_int(level_x1), bits_per_var)
        gray_x2 = gray_int_to_bits(int_to_gray_int(level_x2), bits_per_var)
        genotype = gray_x1 + gray_x2

        population.append(Individual(genotype=genotype, bits_per_var=bits_per_var))

    return population


# ------------------------------------------------------------
# ВЫВОД В КОНСОЛЬ
# ------------------------------------------------------------
def bits_to_string(bits: List[int]) -> str:
    return "".join(str(bit) for bit in bits)


def print_population(population: List[Individual], limit: int = 30) -> None:
    rows = []

    for index, individual in enumerate(population[:limit], start=1):
        rows.append({
            "#": index,
            "Gray x1": bits_to_string(individual.gray_x1),
            "Gray x2": bits_to_string(individual.gray_x2),
            "Генотип": bits_to_string(individual.genotype),
        })
    print(tabulate(rows, headers="keys", tablefmt="grid", showindex=False))


# ------------------------------------------------------------
# ДАННЫЕ ДЛЯ ГРАФИКА
# ------------------------------------------------------------
def get_xy(
    population: List[Individual],
    x1_bounds: Tuple[float, float] = (X1_L, X1_H),
    x2_bounds: Tuple[float, float] = (X2_L, X2_H),
) -> Tuple[List[float], List[float]]:
    xs = []
    ys = []

    for individual in population:
        x1, x2 = decode_individual_to_xy(
            individual,
            x1_bounds=x1_bounds,
            x2_bounds=x2_bounds,
        )
        xs.append(x1)
        ys.append(x2)

    return xs, ys


def build_grid(
    bits_per_var: int,
    x1_bounds: Tuple[float, float],
    x2_bounds: Tuple[float, float],
    draw_full_grid_if_levels_leq: int = DRAW_FULL_GRID_IF_LEVELS_LEQ,
) -> Tuple[List[float], List[float], List[float], List[float], float, float]:
    """
    Возвращает:
    - уровни по x
    - уровни по y
    - узлы сетки по x
    - узлы сетки по y
    - шаг по x
    - шаг по y
    """
    levels_count = 1 << bits_per_var
    max_level = levels_count - 1

    x1_low, x1_high = x1_bounds
    x2_low, x2_high = x2_bounds

    if max_level == 0:
        step_x = 1.0
        step_y = 1.0
    else:
        step_x = (x1_high - x1_low) / max_level
        step_y = (x2_high - x2_low) / max_level

    x_levels = []
    y_levels = []
    grid_x = []
    grid_y = []

    if levels_count <= draw_full_grid_if_levels_leq and max_level > 0:
        for level in range(levels_count):
            x_levels.append(x1_low + level * (x1_high - x1_low) / max_level)
            y_levels.append(x2_low + level * (x2_high - x2_low) / max_level)

        for x_value in x_levels:
            for y_value in y_levels:
                grid_x.append(x_value)
                grid_y.append(y_value)

    return x_levels, y_levels, grid_x, grid_y, step_x, step_y


# ------------------------------------------------------------
# ГРАФИК
# ------------------------------------------------------------
def plot_population(
    population: List[Individual],
    x1_bounds: Tuple[float, float] = (X1_L, X1_H),
    x2_bounds: Tuple[float, float] = (X2_L, X2_H),
    title: str = "Начальная популяция в пространстве x1-x2",
) -> None:
    import matplotlib.pyplot as plt

    if not population:
        raise ValueError("Популяция пуста")

    x_levels, y_levels, grid_x, grid_y, step_x, step_y = build_grid(
        bits_per_var=population[0].bits_per_var,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )

    pop_x, pop_y = get_xy(
        population,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )

    plt.figure(figsize=(10, 8))

    #if grid_x and grid_y:
    #    plt.scatter(grid_x, grid_y, alpha=0.15, label="узлы сетки")

    plt.scatter(pop_x, pop_y, s=20, alpha=1.0, label="начальная популяция")

    plt.title(f"{title} (m={population[0].bits_per_var}, N={len(population)})")
    plt.xlabel("x1")
    plt.ylabel("x2")
    plt.grid(True)

    if x_levels:
        plt.xticks(x_levels, rotation=90 if len(x_levels) > 16 else 0)
    if y_levels:
        plt.yticks(y_levels)

    x1_low, x1_high = x1_bounds
    x2_low, x2_high = x2_bounds
    plt.xlim(x1_low - 0.5 * step_x, x1_high + 0.5 * step_x)
    plt.ylim(x2_low - 0.5 * step_y, x2_high + 0.5 * step_y)

    plt.legend()
    plt.tight_layout()
    plt.show()


# ------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------
if __name__ == "__main__":
    population = generate_initial_population(
        pop_size=POP_SIZE,
        bits_per_var=BITS_PER_VAR,
    )

    print(
        f"\nЭТАП 1: случайная побитовая генерация начальной популяции "
        f"на оси x1/x2 в пространстве Gray-кода "
        f"(POP_SIZE={POP_SIZE}, BITS_PER_VAR={BITS_PER_VAR})"
    )

    print_population(population, limit=30)
    plot_population(population, x1_bounds=(X1_L, X1_H), x2_bounds=(X2_L, X2_H))