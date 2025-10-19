from tabulate import tabulate
import matplotlib.pyplot as plt
import numpy as np
import random


# =============================================================================
# ЗАДАНИЕ 1: Анализ матричной игры
# =============================================================================

def check_saddle_point(matrix):
    """
    Проверяет наличие седловой точки в матричной игре
    """
    row_minima = [min(row) for row in matrix]
    alpha = max(row_minima)

    cols = len(matrix[0])
    col_maxima = [max(matrix[i][j] for i in range(len(matrix))) for j in range(cols)]
    beta = min(col_maxima)

    has_saddle = alpha == beta

    return has_saddle, alpha, beta


def calculate_payment_functions(payment_matrix):
    """
    Вычисляет коэффициенты платежных функций
    """
    num_attacks = len(payment_matrix[0])
    functions = []

    for j in range(num_attacks):
        a1j = payment_matrix[0][j]
        a2j = payment_matrix[1][j]

        k = a1j - a2j
        b = a2j

        function_info = {
            'attack_num': j + 1,
            'a1j': a1j,
            'a2j': a2j,
            'k': k,
            'b': b,
            'equation': f"f(p₁, {j + 1}) = {a1j}*p + {a2j}*(1-p) = {k}p + {b}"
        }
        functions.append(function_info)

    return functions


def plot_payment_functions(functions):
    """
    Строит график платежных функций с верхней огибающей и точкой минимакса
    """
    p = np.linspace(0, 1, 1000)

    plt.figure(figsize=(10, 6))

    colors = ['red', 'blue', 'green', 'orange', 'purple']

    all_y = []

    for i, func in enumerate(functions):
        k = func['k']
        b = func['b']
        y = k * p + b
        all_y.append(y)
        plt.plot(p, y, color=colors[i % len(colors)], linewidth=2, label=f"Атака {func['attack_num']}")

    all_y_array = np.array(all_y)
    # Ищем верхнюю огибающую (максимум для каждого p)
    upper_envelope = np.max(all_y_array, axis=0)

    # Строим верхнюю огибающую
    plt.plot(p, upper_envelope, 'k-', linewidth=3, label='Верхняя огибающая')

    # Находим точку минимакса (минимум верхней огибающей)
    min_index = np.argmin(upper_envelope)
    p_optimal = p[min_index]
    value_optimal = upper_envelope[min_index]

    # Отмечаем точку минимакса на графике
    plt.plot(p_optimal, value_optimal, 'ro', markersize=8,
             label=f'Точка минимакса (p={p_optimal:.3f}, V={value_optimal:.3f})')

    plt.title("График платежных функций с верхней огибающей", fontsize=14)
    plt.xlabel("Вероятность выбора протокола 1 (p)", fontsize=12)
    plt.ylabel("Среднее время передачи", fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xlim(0, 1)

    plt.tight_layout()
    plt.show()

    return p_optimal, value_optimal


def find_optimal_strategies(matrix, p_optimal, value_optimal):
    """
    Находит оптимальные вероятности для игрока B по указанному методу
    """
    active_strategies = []
    tolerance = 0.01

    for j in range(len(matrix[0])):
        a1j = matrix[0][j]
        a2j = matrix[1][j]
        value_at_p = a1j * p_optimal + a2j * (1 - p_optimal)

        if abs(value_at_p - value_optimal) < tolerance:
            active_strategies.append(j + 1)

    if len(active_strategies) < 2:
        differences = []
        for j in range(len(matrix[0])):
            a1j = matrix[0][j]
            a2j = matrix[1][j]
            value_at_p = a1j * p_optimal + a2j * (1 - p_optimal)
            differences.append((j + 1, abs(value_at_p - value_optimal)))

        differences.sort(key=lambda x: x[1])
        active_strategies = [diff[0] for diff in differences[:2]]

    q_probabilities = [0] * len(matrix[0])

    if len(active_strategies) == 2:
        i, j = active_strategies[0] - 1, active_strategies[1] - 1

        a1i, a1j = matrix[0][i], matrix[0][j]
        a2i, a2j = matrix[1][i], matrix[1][j]

        # Решаем уравнения для каждого протокола и находим q1
        # Для протокола 1: q1 * a1i + (1-q1) * a1j = V
        if (a1i - a1j) != 0:
            q1_from_protocol1 = (value_optimal - a1j) / (a1i - a1j)
        else:
            q1_from_protocol1 = 0.5

        # Для протокола 2: q1 * a2i + (1-q1) * a2j = V
        if (a2i - a2j) != 0:
            q1_from_protocol2 = (value_optimal - a2j) / (a2i - a2j)
        else:
            q1_from_protocol2 = 0.5

        # Находим среднее значение q1
        q1_avg = (q1_from_protocol1 + q1_from_protocol2) / 2

        # Округляем до 0.001
        q1 = round(q1_avg, 3)
        q2 = round(1 - q1, 3)

        # Корректируем сумму до 1.000
        if q1 + q2 != 1.0:
            q1 = 1.0 - q2

        q_probabilities[i] = q1
        q_probabilities[j] = q2

    return q_probabilities, active_strategies


# =============================================================================
# ЗАДАНИЕ 2: Моделирование экспериментов
# =============================================================================

def generate_player_A_choices(p_optimal, num_experiments=10000):
    """
    Генерирует массив выборов игрока A на основе вероятности p_optimal
    """
    return [1 if random.random() < p_optimal else 2 for _ in range(num_experiments)]


def generate_player_B_choices(q_probabilities, num_experiments=10000):
    """
    Генерирует массив выборов игрока B на основе вероятностей q_probabilities
    """
    choices = []
    for _ in range(num_experiments):
        rand_val = random.random()
        cumulative_prob = 0
        attack_type = 1

        for j, prob in enumerate(q_probabilities):
            cumulative_prob += prob
            if rand_val <= cumulative_prob:
                attack_type = j + 1
                break

        choices.append(attack_type)

    return choices


def generate_player_B_uniform_choices(active_strategies, num_experiments=10000):
    """
    Генерирует массив выборов игрока B с равномерным распределением между активными стратегиями
    """
    return [random.choice(active_strategies) for _ in range(num_experiments)]


def generate_player_B_all_uniform_choices(num_attacks, num_experiments=10000):
    """
    Генерирует массив выборов игрока B с равномерным распределением между всеми стратегиями
    """
    return [random.randint(1, num_attacks) for _ in range(num_experiments)]


def generate_player_A_wald_choices(optimal_protocol, num_experiments=10000):
    """
    Генерирует массив выборов игрока A, всегда выбирающего оптимальный протокол по Вальду
    """
    return [optimal_protocol for _ in range(num_experiments)]


def calculate_experiment_results(matrix, player_A_choices, player_B_choices):
    """
    Вычисляет результаты экспериментов на основе массивов выборов игроков
    """
    results = []
    cumulative_sum = 0
    cumulative_averages = []

    for i in range(len(player_A_choices)):
        protocol = player_A_choices[i]
        attack_type = player_B_choices[i]

        time = matrix[protocol - 1][attack_type - 1]

        results.append(time)
        cumulative_sum += time
        cumulative_averages.append(cumulative_sum / (i + 1))

    return results, cumulative_averages


def plot_experiment_results_task2(results_A_then_B, cumulative_averages_A_then_B, active_strategies,M):
    """
    Строит графики результатов экспериментов задания 2 в одном окне
    """
    plt.figure(figsize=(12, 6))
    final_average_A_then_B = cumulative_averages_A_then_B[-1]
    # График для эксперимента A затем B
    plt.plot(range(1, len(results_A_then_B) + 1), results_A_then_B, 'b-', alpha=0.7, linewidth=0.8,
             label='Время передачи в эксперименте')
    for i in range(len(M)):
        for j in active_strategies:
            plt.axhline(y=M[i][j-1], color='black', linewidth=2,
                label=f"Время передачи {M[i][j-1]}")
    plt.plot(range(1, len(results_A_then_B) + 1), results_A_then_B, 'b-', alpha=0.7, linewidth=0.8,
             label='Время передачи в эксперименте')
    plt.axhline(y=final_average_A_then_B, color='r', linestyle='--', linewidth=2,
                label=f'Среднее значение ({final_average_A_then_B:.2f})')
    plt.title('Модель 1: Оптимальные стратегии', fontsize=14)
    plt.xlabel('Номер эксперимента', fontsize=12)
    plt.ylabel('Время передачи', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    plt.xlim(1, len(results_A_then_B))
    plt.tight_layout()
    plt.show()

    return final_average_A_then_B


def plot_experiment_results_task3(results_uniform, cumulative_averages_uniform, M):
    """
    Строит график результатов эксперимента задания 3 в отдельном окне
    """
    plt.figure(figsize=(12, 6))

    for i in range(len(M)):
        for j in active_strategies:
            plt.axhline(y=M[i][j-1], color='black', linewidth=2,
                label=f"Время передачи {M[i][j-1]}")
    plt.plot(range(1, len(results_uniform) + 1), results_uniform, 'purple', alpha=0.7, linewidth=0.8,
             label='Время передачи в эксперименте')

    final_average_uniform = cumulative_averages_uniform[-1]
    plt.axhline(y=final_average_uniform, color='r', linestyle='--', linewidth=2,
                label=f'Среднее значение ({final_average_uniform:.2f})')

    plt.title('Модель 2: Эксперимент с равномерным распределением атак (активные стратегии)', fontsize=14)
    plt.xlabel('Номер эксперимента', fontsize=12)
    plt.ylabel('Время передачи', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xlim(1, len(results_uniform))

    plt.tight_layout()
    plt.show()

    return final_average_uniform


def plot_experiment_results_task4(results_all_uniform, cumulative_averages_all_uniform, M):
    """
    Строит график результатов эксперимента задания 4 в отдельном окне
    """
    plt.figure(figsize=(12, 6))

    for i in range(len(M)):
        for j in range(5):
            plt.axhline(y=M[i][j], color='black', linewidth=1,
                label=f"Время передачи {M[i][j]}")

    plt.plot(range(1, len(results_all_uniform) + 1), results_all_uniform, 'orange', alpha=0.7, linewidth=0.8,
             label='Время передачи в эксперименте')

    final_average_all_uniform = cumulative_averages_all_uniform[-1]
    plt.axhline(y=final_average_all_uniform, color='r', linestyle='--', linewidth=2,
                label=f'Среднее значение ({final_average_all_uniform:.2f})')

    plt.title('Модель 3: Эксперимент с равномерным распределением атак (все стратегии)', fontsize=14)
    plt.xlabel('Номер эксперимента', fontsize=12)
    plt.ylabel('Время передачи', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xlim(1, len(results_all_uniform))

    plt.tight_layout()
    plt.show()

    return final_average_all_uniform


def plot_experiment_results_task5(results_wald, cumulative_averages_wald,M, strategy):
    """
    Строит график результатов эксперимента задания 5 в отдельном окне
    """
    plt.figure(figsize=(12, 6))
    for j in active_strategies:
        plt.axhline(y=M[strategy-1][j-1], color='black', linewidth=2,
            label=f"Время передачи {M[strategy-1][j-1]}")
    plt.plot(range(1, len(results_wald) + 1), results_wald, 'brown', alpha=0.7, linewidth=0.8,
             label='Время передачи в эксперименте')

    final_average_wald = cumulative_averages_wald[-1]
    plt.axhline(y=final_average_wald, color='r', linestyle='--', linewidth=2,
                label=f'Среднее значение ({final_average_wald:.2f})')

    plt.title('Модель 4: Эксперимент с оптимальным протоколом по Вальду', fontsize=14)
    plt.xlabel('Номер эксперимента', fontsize=12)
    plt.ylabel('Время передачи', fontsize=12)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    plt.xlim(1, len(results_wald))

    plt.tight_layout()
    plt.show()

    return final_average_wald


def find_optimal_protocol_wald(matrix):
    """
    Находит оптимальный протокол по критерию Вальда
    """
    # Находим максимальное время передачи для каждого протокола
    max_time_protocol1 = max(matrix[0])
    max_time_protocol2 = max(matrix[1])

    # Выбираем протокол с минимальным максимальным временем
    if max_time_protocol1 <= max_time_protocol2:
        optimal_protocol = 1
        max_time = max_time_protocol1
    else:
        optimal_protocol = 2
        max_time = max_time_protocol2

    return optimal_protocol, max_time


# =============================================================================
# ОСНОВНАЯ ПРОГРАММА
# =============================================================================

if __name__ == "__main__":
    M = [
        [21, 12, 15, 23, 18],
        [11, 33, 28, 16, 19]
    ]

    # Вывод исходной матрицы
    headers = ["Протокол/Атака", "Тип 1", "Тип 2", "Тип 3", "Тип 4", "Тип 5"]
    table_data = [
        ["Протокол 1"] + M[0],
        ["Протокол 2"] + M[1]
    ]

    print("ИСХОДНАЯ МАТРИЦА ИГРЫ:")
    print(tabulate(table_data, headers=headers, tablefmt="grid", stralign="center"))

    # Задание 1: Проверка седловой точки
    print("\n" + "=" * 50)
    print("Анализ матричной игры")
    print("=" * 50)

    has_saddle, alpha, beta = check_saddle_point(M)

    print("\nПРОВЕРКА СЕДЛОВОЙ ТОЧКИ:")
    print(f"Нижняя цена игры (α): {alpha}")
    print(f"Верхняя цена игры (β): {beta}")

    if has_saddle:
        print("Седловая точка НАЙДЕНА - игра имеет решение в чистых стратегиях")
    else:
        print("Седловая точка НЕ НАЙДЕНА - необходимо решение в смешанных стратегиях")

    # Уравнения платежных функций
    functions = calculate_payment_functions(M)

    print("\nУРАВНЕНИЯ ПЛАТЕЖНЫХ ФУНКЦИЙ:")
    for func in functions:
        print(func['equation'])

    # Построение графика и нахождение оптимальных вероятностей для A
    p_optimal, value_optimal = plot_payment_functions(functions)

    print(f"\nОПТИМАЛЬНЫЕ ВЕРОЯТНОСТИ ДЛЯ ИГРОКА A:")
    print(f"Вероятность выбора протокола 1 (p): {p_optimal:.3f}")
    print(f"Вероятность выбора протокола 2 (1-p): {1 - p_optimal:.3f}")
    print(f"Цена игры (V): {value_optimal:.3f}")

    # Задание 2: Нахождение оптимальных стратегий для B
    print("\n" + "=" * 50)
    print("Определение оптимальных стратегий для игрока B")
    print("=" * 50)

    q_probabilities, active_strategies = find_optimal_strategies(M, p_optimal, value_optimal)

    print(f"\nАКТИВНЫЕ СТРАТЕГИИ ИГРОКА B: {active_strategies}")

    print(f"\nОПТИМАЛЬНЫЕ ВЕРОЯТНОСТИ ДЛЯ ИГРОКА B:")
    for i, prob in enumerate(q_probabilities):
        if prob > 0:
            print(f"Вероятность выбора атаки {i + 1} (q_{i + 1}): {prob:.3f}")

    # Проверка суммы вероятностей
    total_q = sum(q_probabilities)
    print(f"Сумма вероятностей: {total_q:.3f}")

    # Вывод уравнений для игрока B
    print(f"\nУРАВНЕНИЯ ДЛЯ ИГРОКА B:")
    if len(active_strategies) == 2:
        i, j = active_strategies[0] - 1, active_strategies[1] - 1
        q_i = q_probabilities[i]
        q_j = q_probabilities[j]

        print(f"Для протокола 1: q_{i + 1} × {M[0][i]} + q_{j + 1} × {M[0][j]} = {value_optimal:.3f}")
        print(f"Для протокола 2: q_{i + 1} × {M[1][i]} + q_{j + 1} × {M[1][j]} = {value_optimal:.3f}")
        print(f"q_{i + 1} + q_{j + 1} = 1.000")

    # Генерация массивов выборов игроков
    # Генерируем общий массив выборов игрока A
    player_A_choices = generate_player_A_choices(p_optimal, 10000)

    # Генерируем массивы выборов игрока B для разных экспериментов
    player_B_choices_optimal = generate_player_B_choices(q_probabilities, 10000)
    player_B_choices_uniform = generate_player_B_uniform_choices(active_strategies, 10000)
    player_B_choices_all_uniform = generate_player_B_all_uniform_choices(len(M[0]), 10000)
    # Проведение экспериментов задания 2
    print("\n" + "=" * 50)
    print("ПРОВЕДЕНИЕ ЭКСПЕРИМЕНТОВ")
    print("=" * 50)

    # Эксперимент 1: A затем B (оптимальные стратегии)
    results_A_then_B, cumulative_averages_A_then_B = calculate_experiment_results(
        M, player_A_choices, player_B_choices_optimal
    )
    final_average_A_then_B = plot_experiment_results_task2(results_A_then_B, cumulative_averages_A_then_B,
                                                           active_strategies, M)

    print(f"\nРЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТОВ МОДЕЛИ 1:")
    print(f"Теоретическая цена игры: {value_optimal:.3f}")
    print(f"Практическое среднее время: {final_average_A_then_B:.3f}")

    # Сравнение результатов задания 2
    difference_optimal = abs(final_average_A_then_B - value_optimal)

    print(f"\nСРАВНЕНИЕ РЕЗУЛЬТАТОВ МОДЕЛИ 1:")
    print(f"Разница между теоретической и практической ценой игры (оптимальные стратегии): {difference_optimal:.3f}")

    if difference_optimal < 0.5:
        print("Практический результат с оптимальными стратегиями близок к теоретическому")
    else:
        print("Заметное расхождение между теоретическим и практическим результатами с оптимальными стратегиями")

    # =============================================================================
    # ЗАДАНИЕ 2: Эксперимент с равномерным распределением атак (активные стратегии)
    # =============================================================================

    print("\n" + "=" * 50)
    print("ЗАДАНИЕ 2: Эксперимент с равномерным распределением атак (активные стратегии)")
    print("=" * 50)

    # Эксперимент 3: равномерное распределение атак (активные стратегии)
    results_uniform, cumulative_averages_uniform = calculate_experiment_results(
        M, player_A_choices, player_B_choices_uniform
    )

    final_average_uniform = plot_experiment_results_task3(results_uniform, cumulative_averages_uniform,M)

    print(f"\nРЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА МОДЕЛИ 2:")
    print(
        f"Практическое среднее время (равномерное распределение атак, активные стратегии): {final_average_uniform:.3f}")
    print(f"Практическое среднее время (оптимальные стратегии): {final_average_A_then_B:.3f}")

    # Сравнение результатов задания 3
    difference_uniform = final_average_uniform - final_average_A_then_B

    print(f"\nСРАВНЕНИЕ РЕЗУЛЬТАТОВ МОДЕЛИ 2:")
    print(f"Разница между равномерным (активные стратегии) и оптимальным распределением атак: {difference_uniform:.3f}")

    if difference_uniform < 0:
        print(
            "Реальная цена игры с равномерным распределением атак (активные стратегии) НИЖЕ, чем с оптимальными стратегиями")
    else:
        print(
            "Реальная цена игры с равномерным распределением атак (активные стратегии) ВЫШЕ, чем с оптимальными стратегиями")

    # =============================================================================
    # ЗАДАНИЕ 4: Эксперимент с равномерным распределением атак (все стратегии)
    # =============================================================================

    print("\n" + "=" * 50)
    print("ЗАДАНИЕ 3: Эксперимент с равномерным распределением атак (все стратегии)")
    print("=" * 50)

    # Эксперимент 4: равномерное распределение атак (все стратегии)
    results_all_uniform, cumulative_averages_all_uniform = calculate_experiment_results(
        M, player_A_choices, player_B_choices_all_uniform
    )

    final_average_all_uniform = plot_experiment_results_task4(results_all_uniform, cumulative_averages_all_uniform,M)

    print(f"\nРЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА МОДЕЛИ 3:")
    print(
        f"Практическое среднее время (равномерное распределение атак, все стратегии): {final_average_all_uniform:.3f}")
    print(f"Практическое среднее время (оптимальные стратегии): {final_average_A_then_B:.3f}")

    # Сравнение результатов задания 4
    difference_all_uniform = final_average_all_uniform - final_average_A_then_B

    print(f"\nСРАВНЕНИЕ РЕЗУЛЬТАТОВ МОДЕЛИ 3:")
    print(f"Разница между равномерным (все стратегии) и оптимальным распределением атак: {difference_all_uniform:.3f}")

    if difference_all_uniform < 0:
        print(
            "Реальная цена игры с равномерным распределением атак (все стратегии) НИЖЕ, чем с оптимальными стратегиями")
    else:
        print(
            "Реальная цена игры с равномерным распределением атак (все стратегии) ВЫШЕ, чем с оптимальными стратегиями")

    # =============================================================================
    # ЗАДАНИЕ 5: Эксперимент с оптимальным протоколом по критерию Вальда
    # =============================================================================

    print("\n" + "=" * 50)
    print("ЗАДАНИЕ 4: Эксперимент с оптимальным протоколом по критерию Вальда")
    print("=" * 50)

    # Находим оптимальный протокол по критерию Вальда
    optimal_protocol_wald, max_time_wald = find_optimal_protocol_wald(M)

    print(f"\nОПТИМАЛЬНЫЙ ПРОТОКОЛ ПО КРИТЕРИЮ ВАЛЬДА:")
    print(f"Максимальное время передачи для протокола 1: {max(M[0])}")
    print(f"Максимальное время передачи для протокола 2: {max(M[1])}")
    print(f"Оптимальный протокол: {optimal_protocol_wald}")
    print(f"Максимальное гарантированное время: {max_time_wald}")

    # Генерируем массив выборов игрока A для критерия Вальда
    player_A_choices_wald = generate_player_A_wald_choices(optimal_protocol_wald, 10000)

    # Эксперимент 5: оптимальный протокол по Вальду
    results_wald, cumulative_averages_wald = calculate_experiment_results(
        M, player_A_choices_wald, player_B_choices_optimal
    )
    final_average_wald = plot_experiment_results_task5(results_wald, cumulative_averages_wald,
                                                       M, player_A_choices_wald[0])

    print(f"\nРЕЗУЛЬТАТЫ ЭКСПЕРИМЕНТА МОДЕЛИ 4:")
    print(f"Практическое среднее время (оптимальный протокол по Вальду): {final_average_wald:.3f}")
    print(f"Практическое среднее время (оптимальные стратегии): {final_average_A_then_B:.3f}")

    # Сравнение результатов задания 5
    difference_wald = final_average_wald - final_average_A_then_B

    print(f"\nСРАВНЕНИЕ РЕЗУЛЬТАТОВ МОДЕЛИ 4:")
    print(f"Разница между оптимальным протоколом по Вальду и оптимальными стратегиями: {difference_wald:.3f}")

    if difference_wald < 0:
        print("Реальная цена игры с оптимальным протоколом по Вальду НИЖЕ, чем с оптимальными стратегиями")
    else:
        print("Реальная цена игры с оптимальным протоколом по Вальду ВЫШЕ, чем с оптимальными стратегиями")

    # =============================================================================
    # ИТОГОВОЕ СРАВНЕНИЕ ВСЕХ ЭКСПЕРИМЕНТОВ
    # =============================================================================

    print("\n" + "=" * 50)
    print("ИТОГОВОЕ СРАВНЕНИЕ ВСЕХ ЭКСПЕРИМЕНТОВ")
    print("=" * 50)

    print(f"Теоретическая цена игры: {value_optimal:.3f}")
    print(f"Оптимальные стратегии (A затем B): {final_average_A_then_B:.3f}")
    print(f"Равномерное распределение (активные стратегии): {final_average_uniform:.3f}")
    print(f"Равномерное распределение (все стратегии): {final_average_all_uniform:.3f}")
    print(f"Оптимальный протокол по Вальду: {final_average_wald:.3f}")

    print(
        f"\nЛУЧШИЙ РЕЗУЛЬТАТ (ДЛЯ B): {max(final_average_A_then_B, final_average_uniform, final_average_all_uniform, final_average_wald):.3f}")