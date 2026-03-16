from typing import Dict, List, Tuple
import random

import config as cfg
import stage_1 as st1
import stage_2 as st2


# ============================================================
# НАСТРОЙКИ ЭТАПА 3
# ============================================================
SELECTION_GROUP_SIZE = cfg.SELECTION_GROUP_SIZE
PARENTS_PER_GROUP = cfg.PARENTS_PER_GROUP
SELECTION_CYCLES = cfg.SELECTION_CYCLES
MUTATION_PROBABILITY = cfg.MUTATION_PROBABILITY
PSI = cfg.PSI
# ============================================================


# ------------------------------------------------------------
# ВЫБОР РАЗМЕРА ГРУППЫ
# ------------------------------------------------------------
def choose_dynamic_group_size(
    population_size: int,
    k_group: int = SELECTION_GROUP_SIZE,
) -> int:
    """
    Проверяет и возвращает допустимый размер группы.

    Требования:
    - 2 <= k_group <= 100
    - population_size % k_group == 0
    """
    if population_size <= 0:
        raise ValueError("population_size должен быть > 0")
    if k_group < 2 or k_group > 100:
        raise ValueError("k_group должен быть в диапазоне 2..100.")
    if population_size % k_group != 0:
        raise ValueError(
            f"Размер популяции {population_size} не делится на k_group={k_group}."
        )

    return k_group


# ------------------------------------------------------------
# ДИНАМИЧЕСКАЯ РУЛЕТКА ДЛЯ РАСПРЕДЕЛЕНИЯ ПО ГРУППАМ
# ------------------------------------------------------------
def build_group_roulette_intervals(
    active_group_ids: List[int],
) -> List[Tuple[int, float, float]]:
    """
    Равномерно распределяет активные группы на интервале [0, 1).
    """
    if not active_group_ids:
        return []

    intervals = []
    width = 1.0 / len(active_group_ids)
    left = 0.0

    for i, group_id in enumerate(active_group_ids):
        if i == len(active_group_ids) - 1:
            right = 1.0
        else:
            right = left + width

        intervals.append((group_id, left, right))
        left = right

    return intervals


def choose_group_by_roulette(
    intervals: List[Tuple[int, float, float]],
) -> int:
    """
    Выбирает группу по рулетке.
    """
    if not intervals:
        raise ValueError("Нет активных групп для распределения.")

    r = random.random()

    for group_id, left, right in intervals:
        if left <= r < right:
            return group_id

    return intervals[-1][0]


# ------------------------------------------------------------
# ФОРМИРОВАНИЕ ГРУПП
# ------------------------------------------------------------
def form_tournament_groups(
    population: List[st1.Individual],
    k_group: int,
) -> List[List[Tuple[int, st1.Individual]]]:
    """
    Делит популяцию на группы по k_group особей.

    Возвращает список групп.
    Каждая группа хранит:
        (индекс особи в текущей популяции, объект особи)
    """
    population_size = len(population)

    if population_size == 0:
        raise ValueError("Популяция пуста.")
    if k_group < 2 or k_group > 100:
        raise ValueError("k_group должен быть в диапазоне 2..100.")
    if population_size % k_group != 0:
        raise ValueError(
            f"Размер популяции {population_size} не делится на k_group={k_group}."
        )

    number_of_groups = population_size // k_group

    groups: List[List[Tuple[int, st1.Individual]]] = []
    for _ in range(number_of_groups):
        groups.append([])

    active_group_ids = list(range(number_of_groups))
    intervals = build_group_roulette_intervals(active_group_ids)

    for source_index, individual in enumerate(population, start=1):
        group_id = choose_group_by_roulette(intervals)
        groups[group_id].append((source_index, individual))

        if len(groups[group_id]) == k_group:
            active_group_ids.remove(group_id)
            intervals = build_group_roulette_intervals(active_group_ids)

    return groups


# ------------------------------------------------------------
# FITNESS ВНУТРИ ГРУППЫ
# ------------------------------------------------------------
def build_group_objectives(
    group: List[Tuple[int, st1.Individual]],
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> List[Tuple[float, float]]:
    objs: List[Tuple[float, float]] = []

    for _, individual in group:
        x1_value, x2_value = st1.decode_individual_to_xy(
            individual,
            x1_bounds=x1_bounds,
            x2_bounds=x2_bounds,
        )
        objs.append((st2.f1(x1_value, x2_value), st2.f2(x1_value, x2_value)))

    return objs


def compute_group_fitness(
    group: List[Tuple[int, st1.Individual]],
    psi: float = PSI,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> Tuple[List[Tuple[float, float]], List[int], List[float]]:
    """
    Считает fitness внутри группы по той же формуле, что на этапе 2.

    Возвращает:
    - objs: значения (f1, f2)
    - b_list: число точек, доминирующих данную точку внутри группы
    - fitness_list: значения Phi внутри группы
    """
    if psi < 0:
        raise ValueError("Для fitness в диапазоне [0, 1] требуется psi >= 0.")

    group_size = len(group)
    if group_size == 0:
        return [], [], []

    objs = build_group_objectives(
        group,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )

    b_list = st2.count_dominators_2d(objs)

    fitness_list = [1.0] * group_size

    if group_size == 1:
        fitness_list[0] = 1.0
    else:
        denom = group_size - 1
        for i in range(group_size):
            base = 1.0 + (b_list[i] / denom)
            if psi == 0:
                fitness_list[i] = 1.0
            else:
                fitness_list[i] = 1.0 / (base ** psi)

    return objs, b_list, fitness_list


# ------------------------------------------------------------
# СТАТИЧЕСКАЯ РУЛЕТКА ВНУТРИ ГРУППЫ
# ------------------------------------------------------------
def build_static_roulette_intervals(
    fitness_list: List[float],
) -> List[Tuple[int, float, float]]:
    """
    Строит статическую рулетку по fitness.
    """
    if not fitness_list:
        return []

    total_fitness = sum(fitness_list)

    if total_fitness <= 0:
        probability = 1.0 / len(fitness_list)
        probabilities = [probability] * len(fitness_list)
    else:
        probabilities = []
        for value in fitness_list:
            probabilities.append(value / total_fitness)

    intervals = []
    left = 0.0

    for i, probability in enumerate(probabilities):
        if i == len(probabilities) - 1:
            right = 1.0
        else:
            right = left + probability

        intervals.append((i, left, right))
        left = right

    return intervals


def choose_member_by_static_roulette(
    intervals: List[Tuple[int, float, float]],
) -> int:
    """
    Выбирает индекс особи внутри группы по статической рулетке.
    """
    if not intervals:
        raise ValueError("Нет интервалов рулетки для выбора родителя.")

    r = random.random()

    for member_index, left, right in intervals:
        if left <= r < right:
            return member_index

    return intervals[-1][0]


def select_parents_from_group(
    group: List[Tuple[int, st1.Individual]],
    parents_per_group: int = PARENTS_PER_GROUP,
    psi: float = PSI,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> List[st1.Individual]:
    """
    Выбирает заданное число родителей из одной группы методом
    статической рулетки.

    Отбор идёт с возвращением.
    """
    if not group:
        raise ValueError("Группа пуста.")
    if parents_per_group <= 0:
        raise ValueError("parents_per_group должен быть > 0.")

    _, _, fitness_list = compute_group_fitness(
        group,
        psi=psi,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )

    intervals = build_static_roulette_intervals(fitness_list)

    selected_parents: List[st1.Individual] = []
    for _ in range(parents_per_group):
        member_index = choose_member_by_static_roulette(intervals)
        _, individual = group[member_index]
        selected_parents.append(individual)

    return selected_parents


# ------------------------------------------------------------
# СБОР РОДИТЕЛЕЙ ПО ОДНОМУ ЦИКЛУ
# ------------------------------------------------------------
def build_parent_population_for_one_cycle(
    population: List[st1.Individual],
    k_group: int,
    parents_per_group: int = PARENTS_PER_GROUP,
    psi: float = PSI,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> Tuple[List[st1.Individual], List[List[Tuple[int, st1.Individual]]]]:
    """
    Один цикл:
    - делит исходную популяцию на группы,
    - в каждой группе выбирает заданное число родителей,
    - склеивает их в общий массив родителей для данного цикла.
    """
    groups = form_tournament_groups(population, k_group=k_group)

    cycle_parents: List[st1.Individual] = []

    for group in groups:
        selected = select_parents_from_group(
            group,
            parents_per_group=parents_per_group,
            psi=psi,
            x1_bounds=x1_bounds,
            x2_bounds=x2_bounds,
        )
        cycle_parents.extend(selected)

    return cycle_parents, groups


def collect_parents_over_cycles(
    initial_population: List[st1.Individual],
    cycles: int = SELECTION_CYCLES,
    k_group: int | None = None,
    parents_per_group: int = PARENTS_PER_GROUP,
    parent_target_count: int | None = None,
    psi: float = PSI,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> Tuple[List[st1.Individual], List[dict], int, int]:
    """
    Многократно выполняет отбор родителей по одной и той же
    исходной популяции.

    За один цикл формируется:
        number_of_groups * parents_per_group
    родителей.

    Если parent_target_count задан, функция проверяет, что настроек
    достаточно для получения нужного числа родителей, и при необходимости
    обрезает итоговый массив до target_count.
    """
    population_size = len(initial_population)
    cycles = int(cycles)
    parents_per_group = int(parents_per_group)
    if population_size == 0:
        raise ValueError("Начальная популяция пуста.")
    if cycles <= 0:
        raise ValueError("cycles должен быть > 0.")
    if parents_per_group <= 0:
        raise ValueError("parents_per_group должен быть > 0.")

    if k_group is None:
        k_group = choose_dynamic_group_size(
            population_size=population_size,
            k_group=SELECTION_GROUP_SIZE,
        )
    else:
        k_group = choose_dynamic_group_size(
            population_size=population_size,
            k_group=k_group,
        )

    number_of_groups = population_size // k_group
    total_parents_planned = cycles * number_of_groups * parents_per_group

    if parent_target_count is not None:
        if parent_target_count <= 0:
            raise ValueError("parent_target_count должен быть > 0.")
        if total_parents_planned < parent_target_count:
            raise ValueError(
                f"При cycles={cycles}, k_group={k_group} и "
                f"parents_per_group={parents_per_group} можно получить только "
                f"{total_parents_planned} родителей, а требуется не менее "
                f"{parent_target_count}."
            )

    all_parents: List[st1.Individual] = []
    history: List[dict] = []

    for cycle_number in range(1, cycles + 1):
        cycle_parents, groups = build_parent_population_for_one_cycle(
            population=initial_population,
            k_group=k_group,
            parents_per_group=parents_per_group,
            psi=psi,
            x1_bounds=x1_bounds,
            x2_bounds=x2_bounds,
        )

        expected_cycle_parents = number_of_groups * parents_per_group
        if len(cycle_parents) != expected_cycle_parents:
            raise RuntimeError(
                f"Некорректное число родителей на цикле {cycle_number}: "
                f"{len(cycle_parents)} вместо {expected_cycle_parents}."
            )

        all_parents.extend(cycle_parents)

        history.append({
            "cycle": cycle_number,
            "groups_count": len(groups),
            "group_size": k_group,
            "parents_per_group": parents_per_group,
            "parents_selected": len(cycle_parents),
        })

    if parent_target_count is not None and len(all_parents) > parent_target_count:
        all_parents = all_parents[:parent_target_count]

    return all_parents, history, k_group, parents_per_group


# ------------------------------------------------------------
# ТРЁХТОЧЕЧНЫЙ КРОССОВЕР
# ------------------------------------------------------------
def generate_crossover_points_for_pair(
    bits_per_var: int,
) -> Tuple[int, int, int]:
    """
    Генерирует точки кроссовера для ОДНОЙ пары родителей.

    point2 фиксирован и отделяет x1 от x2.
    point1 случайно делит x1.
    point3 случайно делит x2.
    """
    if bits_per_var < 2:
        raise ValueError(
            "Для трёхточечного кроссовера bits_per_var должен быть >= 2."
        )

    genotype_length = 2 * bits_per_var

    point1 = random.randint(1, bits_per_var - 1)
    point2 = bits_per_var
    point3 = random.randint(bits_per_var + 1, genotype_length - 1)

    return point1, point2, point3


def three_point_crossover(
    parent1: st1.Individual,
    parent2: st1.Individual,
    point1: int,
    point2: int,
    point3: int,
) -> Tuple[List[int], List[int]]:
    """
    Выполняет трёхточечный кроссовер по заранее заданным точкам.

    point2 фиксирован и отделяет x1 от x2.
    point1 делит x1.
    point3 делит x2.

    После этого меняются нечётные фрагменты:
    - фрагмент 1
    - фрагмент 3
    """
    if parent1.bits_per_var != parent2.bits_per_var:
        raise ValueError("У родителей разная длина кодирования.")

    genotype_length = len(parent1.genotype)

    if not (1 <= point1 < point2 < point3 < genotype_length):
        raise ValueError(
            f"Некорректные точки кроссовера: point1={point1}, "
            f"point2={point2}, point3={point3}, genotype_length={genotype_length}"
        )

    g1 = parent1.genotype
    g2 = parent2.genotype

    g1_part1 = g1[:point1]
    g1_part2 = g1[point1:point2]
    g1_part3 = g1[point2:point3]
    g1_part4 = g1[point3:]

    g2_part1 = g2[:point1]
    g2_part2 = g2[point1:point2]
    g2_part3 = g2[point2:point3]
    g2_part4 = g2[point3:]

    child1_genotype = g2_part1 + g1_part2 + g2_part3 + g1_part4
    child2_genotype = g1_part1 + g2_part2 + g1_part3 + g2_part4

    return child1_genotype, child2_genotype


# ------------------------------------------------------------
# МУТАЦИЯ
# ------------------------------------------------------------
def mutate_genotype(
    genotype: List[int],
    mutation_probability: float = MUTATION_PROBABILITY,
) -> List[int]:
    """
    С вероятностью mutation_probability инвертирует один случайный бит.

    В адаптивном варианте сама вероятность mutation_probability
    вычисляется на стадии 4 как функция текущей доли элитных точек.
    """
    new_genotype = genotype.copy()

    if random.random() < mutation_probability:
        bit_index = random.randrange(len(new_genotype))
        new_genotype[bit_index] = 1 - new_genotype[bit_index]

    return new_genotype


# ------------------------------------------------------------
# ФОРМИРОВАНИЕ ПОТОМКОВ
# ------------------------------------------------------------
def build_offspring_population(
    parent_population: List[st1.Individual],
    mutation_probability: float = MUTATION_PROBABILITY,
) -> Tuple[List[st1.Individual], Dict[str, object]]:
    """
    1. Случайно разбивает родителей на пары
    2. Для каждой пары генерирует СВОИ точки трёхточечного кроссовера
    3. Выполняет кроссовер
    4. Применяет мутацию
    5. Возвращает популяцию потомков

    point2 для каждой пары фиксирован и равен bits_per_var.
    Для вывода возвращается краткая сводка по использованным точкам.
    """
    population_size = len(parent_population)

    if population_size == 0:
        raise ValueError("Популяция родителей пуста.")
    if population_size % 2 != 0:
        raise ValueError("Размер популяции родителей должен быть чётным.")

    bits_per_var = parent_population[0].bits_per_var
    for parent in parent_population:
        if parent.bits_per_var != bits_per_var:
            raise ValueError("У особей в популяции родителей разная длина кодирования.")

    shuffled_parents = parent_population.copy()
    random.shuffle(shuffled_parents)

    offspring_population: List[st1.Individual] = []
    used_points: List[Tuple[int, int, int]] = []

    for i in range(0, population_size, 2):
        parent1 = shuffled_parents[i]
        parent2 = shuffled_parents[i + 1]

        point1, point2, point3 = generate_crossover_points_for_pair(bits_per_var)
        used_points.append((point1, point2, point3))

        child1_genotype, child2_genotype = three_point_crossover(
            parent1,
            parent2,
            point1=point1,
            point2=point2,
            point3=point3,
        )

        child1_genotype = mutate_genotype(
            child1_genotype,
            mutation_probability=mutation_probability,
        )
        child2_genotype = mutate_genotype(
            child2_genotype,
            mutation_probability=mutation_probability,
        )

        child1 = st1.Individual(
            genotype=child1_genotype,
            bits_per_var=parent1.bits_per_var,
        )
        child2 = st1.Individual(
            genotype=child2_genotype,
            bits_per_var=parent2.bits_per_var,
        )

        offspring_population.append(child1)
        offspring_population.append(child2)

    point1_values = [points[0] for points in used_points]
    point3_values = [points[2] for points in used_points]

    crossover_summary: Dict[str, object] = {
        "mode": "per_pair",
        "pairs_count": len(used_points),
        "point2_fixed": bits_per_var,
        "point1_range": (min(point1_values), max(point1_values)),
        "point3_range": (min(point3_values), max(point3_values)),
    }

    return offspring_population, crossover_summary


# ------------------------------------------------------------
# ПОЛНЫЙ ЭТАП 3
# ------------------------------------------------------------
def run_stage3(
    initial_population: List[st1.Individual],
    cycles: int = SELECTION_CYCLES,
    k_group: int | None = None,
    parents_per_group: int = PARENTS_PER_GROUP,
    parent_target_count: int | None = None,
    psi: float = PSI,
    mutation_probability: float = MUTATION_PROBABILITY,
    x1_bounds: Tuple[float, float] = (st1.X1_L, st1.X1_H),
    x2_bounds: Tuple[float, float] = (st1.X2_L, st1.X2_H),
) -> Tuple[List[st1.Individual], List[st1.Individual], List[dict], int, int, Dict[str, object]]:
    """
    Полный этап 3:

    1. Берётся исходная популяция этапа 1
    2. Популяция многократно случайно разбивается на группы по k_group,
       и на каждом цикле из каждой группы выбирается заданное
       число особей по fitness
    3. Все выбранные родители склеиваются в один массив
    4. Над этим массивом выполняются:
       - случайное разбиение на пары
       - трёхточечный кроссовер
       - мутация

    Возвращает:
    - parent_population: итоговый массив родителей
    - offspring_population: итоговая популяция потомков
    - history: история циклов отбора
    - k_group: фактически использованный размер группы
    - parents_per_group: сколько родителей брали из группы за цикл
    - crossover_points: сводка по точкам кроссовера
    """
    if not initial_population:
        raise ValueError("Начальная популяция пуста.")

    if parent_target_count is None:
        parent_target_count = len(initial_population)

    parent_population, history, k_group, parents_per_group = collect_parents_over_cycles(
        initial_population=initial_population,
        cycles=cycles,
        k_group=k_group,
        parents_per_group=parents_per_group,
        parent_target_count=parent_target_count,
        psi=psi,
        x1_bounds=x1_bounds,
        x2_bounds=x2_bounds,
    )

    if len(parent_population) % 2 != 0:
        raise RuntimeError(
            f"Размер массива родителей {len(parent_population)} должен быть чётным "
            f"для выполнения кроссовера."
        )

    offspring_population, crossover_points = build_offspring_population(
        parent_population=parent_population,
        mutation_probability=mutation_probability,
    )

    if len(offspring_population) != len(parent_population):
        raise RuntimeError(
            f"Размер популяции потомков {len(offspring_population)} "
            f"не совпадает с размером массива родителей {len(parent_population)}."
        )

    return (
        parent_population,
        offspring_population,
        history,
        k_group,
        parents_per_group,
        crossover_points,
    )


# ------------------------------------------------------------
# ВЫВОД В КОНСОЛЬ
# ------------------------------------------------------------
def print_stage3_history(history: List[dict]) -> None:
    rows = []

    for item in history:
        rows.append({
            "Цикл": item["cycle"],
            "Число групп": item["groups_count"],
            "Размер группы": item["group_size"],
            "Родителей из группы": item["parents_per_group"],
            "Всего родителей за цикл": item["parents_selected"],
        })

    try:
        from tabulate import tabulate
        print(tabulate(rows, headers="keys", tablefmt="grid", showindex=False))
    except Exception:
        print("Цикл | Число групп | Размер группы | Родителей из группы | Всего родителей за цикл")
        print("-" * 140)
        for row in rows:
            print(
                f"{row['Цикл']} | {row['Число групп']} | {row['Размер группы']} | "
                f"{row['Родителей из группы']} | {row['Всего родителей за цикл']}"
            )


def print_sample_population(
    population: List[st1.Individual],
    title: str,
    limit: int = 30,
) -> None:
    print(f"\n{title}")
    st1.print_population(population, limit=limit)


# ------------------------------------------------------------
# ЗАПУСК
# ------------------------------------------------------------
if __name__ == "__main__":
    initial_population = st1.generate_initial_population(
        pop_size=st1.POP_SIZE,
        bits_per_var=st1.BITS_PER_VAR,
    )

    (
        parent_population,
        offspring_population,
        history,
        selected_k_group,
        parents_per_group,
        crossover_points,
    ) = run_stage3(
        initial_population=initial_population,
        cycles=SELECTION_CYCLES,
        k_group=None,
        parent_target_count=len(initial_population),
        psi=PSI,
        mutation_probability=MUTATION_PROBABILITY,
        x1_bounds=(st1.X1_L, st1.X1_H),
        x2_bounds=(st1.X2_L, st1.X2_H),
    )

    print("\nЭТАП 3: многократный отбор родителей + кроссовер + мутация")
    print(f"Размер исходной популяции = {len(initial_population)}")
    print(f"Число циклов отбора = {len(history)}")
    print(f"Размер группы k_group = {selected_k_group}")
    print(f"Родителей из одной группы за цикл = {parents_per_group}")
    print(f"Размер массива родителей = {len(parent_population)}")
    print(f"Размер популяции потомков = {len(offspring_population)}")
    print(f"Вероятность мутации = {MUTATION_PROBABILITY}")
    print(f"Сводка по точкам кроссовера: {crossover_points}")

    print_stage3_history(history)

    print_sample_population(
        parent_population,
        title="Первые 30 особей массива родителей:",
        limit=30,
    )

    print_sample_population(
        offspring_population,
        title="Первые 30 особей популяции потомков:",
        limit=30,
    )
