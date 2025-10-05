import matplotlib.pyplot as plt
import numpy as np
from itertools import combinations


def calculate_payment_functions(payment_matrix):
    """
    Вычисляет коэффициенты платежных функций на основе платежной матрицы
    """
    num_attacks = len(payment_matrix[0])
    functions = []

    for j in range(num_attacks):
        # Получаем значения для текущей атаки
        a1j = payment_matrix[0][j]
        a2j = payment_matrix[1][j]

        # Вычисляем коэффициенты линейной функции: k*p + b
        k = a1j - a2j
        b = a2j

        # Формируем описание функции
        function_info = {
            'attack_num': j + 1,
            'a1j': a1j,
            'a2j': a2j,
            'k': k,
            'b': b,
            'equation': f"W(B{j + 1})(p) = {a1j}*p + {a2j}*(1-p) = {k}p + {b}"
        }
        functions.append(function_info)

    return functions


def find_intersections(functions):
    intersections = []

    # Перебираем все пары функций
    for i, j in combinations(range(len(functions)), 2):
        func1 = functions[i]
        func2 = functions[j]

        # Проверяем, не параллельны ли прямые
        if func1['k'] != func2['k']:
            # Находим точку пересечения: k1*p + b1 = k2*p + b2
            p_intersect = (func2['b'] - func1['b']) / (func1['k'] - func2['k'])

            # Проверяем, что точка в допустимом диапазоне
            if 0 <= p_intersect <= 1:
                # Вычисляем значение в точке пересечения
                value = func1['k'] * p_intersect + func1['b']

                intersection_info = {
                    'p': p_intersect,
                    'value': value,
                    'func1': func1['attack_num'],
                    'func2': func2['attack_num'],
                    'label': f"B{func1['attack_num']}∩B{func2['attack_num']}"
                }
                intersections.append(intersection_info)

    return intersections


def find_envelope_points(intersections, functions, p_values):
    # Вычисляем значения всех функций для всех p
    all_values = []
    for func in functions:
        func_values = []
        for p in p_values:
            value = func['k'] * p + func['b']
            func_values.append(value)
        all_values.append(func_values)

    # Вычисляем верхнюю огибающую (максимум в каждой точке)
    upper_envelope = []
    for i in range(len(p_values)):
        max_val = -float('inf')
        for j in range(len(functions)):
            if all_values[j][i] > max_val:
                max_val = all_values[j][i]
        upper_envelope.append(max_val)

    # Вычисляем нижнюю огибающую (минимум в каждой точке)
    lower_envelope = []
    for i in range(len(p_values)):
        min_val = float('inf')
        for j in range(len(functions)):
            if all_values[j][i] < min_val:
                min_val = all_values[j][i]
        lower_envelope.append(min_val)

    # Находим точки пересечения, принадлежащие огибающим
    upper_points = []
    lower_points = []

    for intersection in intersections:
        p = intersection['p']
        value = intersection['value']

        # Находим ближайшую точку в дискретном массиве
        idx = np.argmin(np.abs(p_values - p))

        # Проверяем принадлежность к верхней огибающей (с допуском)
        if abs(upper_envelope[idx] - value) < 0.1:
            upper_points.append(intersection)

        # Проверяем принадлежность к нижней огибающей (с допуском)
        if abs(lower_envelope[idx] - value) < 0.1:
            lower_points.append(intersection)

    # Сортируем точки по координате p
    upper_points.sort(key=lambda x: x['p'])
    lower_points.sort(key=lambda x: x['p'])

    return upper_points, lower_points, upper_envelope, lower_envelope


def plot_payment_functions_with_envelopes(payment_matrix):

    # Вычисляем платежные функции
    functions = calculate_payment_functions(payment_matrix)

    # Находим точки пересечения
    intersections = find_intersections(functions)

    # Создаем диапазон значений p от 0 до 1
    p_values = np.arange(0, 1.01, 0.01)

    # Находим точки огибающих
    upper_points, lower_points, upper_envelope, lower_envelope = find_envelope_points(
        intersections, functions, p_values)

    # Создаем график
    plt.figure(figsize=(14, 10))

    # Цвета для разных типов атак
    colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

    # Строим графики для каждой атаки
    for i, func in enumerate(functions):
        # Вычисляем значения функции для всех p
        w_values = []
        for p in p_values:
            w = func['k'] * p + func['b']
            w_values.append(w)

        # Строим график
        color_index = i % len(colors)
        plt.plot(p_values, w_values,
                 color=colors[color_index],
                 linewidth=1.5,
                 alpha=0.7,
                 label=f'Атака {func["attack_num"]}')

    # Строим верхнюю огибающую
    plt.plot(p_values, upper_envelope, 'red', linewidth=3, label='Верхняя огибающая')

    # Строим нижнюю огибающую
    plt.plot(p_values, lower_envelope, 'blue', linewidth=3, label='Нижняя огибающая')

    # Отмечаем точки верхней огибающей (красные) и нумеруем их
    for i, point in enumerate(upper_points):
        plt.plot(point['p'], point['value'], 'ro', markersize=8, markeredgecolor='darkred', markeredgewidth=2)
        plt.annotate(f'X{i + 1}',
                     xy=(point['p'], point['value']),
                     xytext=(8, 8),
                     textcoords='offset points',
                     fontsize=10,
                     fontweight='bold',
                     color='red')

    # Отмечаем точки нижней огибающей (зеленые) и нумеруем их
    for i, point in enumerate(lower_points):
        plt.plot(point['p'], point['value'], 'go', markersize=8, markeredgecolor='darkgreen', markeredgewidth=2)
        plt.annotate(f'Y{i + 1}',
                     xy=(point['p'], point['value']),
                     xytext=(8, 8),
                     textcoords='offset points',
                     fontsize=10,
                     fontweight='bold',
                     color='green')

    # Находим и отмечаем точку минимакса (минимум верхней огибающей)
    min_upper_value = min(upper_envelope)
    min_upper_index = upper_envelope.index(min_upper_value)
    min_upper_p = p_values[min_upper_index]

    plt.plot(min_upper_p, min_upper_value, 's', markersize=12, markerfacecolor='none', markeredgecolor='black',
             markeredgewidth=3)
    plt.annotate(f'Минимакс\np={min_upper_p:.3f}\nV={min_upper_value:.3f}',
                 xy=(min_upper_p, min_upper_value),
                 xytext=(15, 15),
                 textcoords='offset points',
                 fontsize=10,
                 bbox=dict(boxstyle="round,pad=0.3", fc="lightcoral", alpha=0.7),
                 arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0.2"))

    # Создаем текст с координатами точек пересечения
    intersection_text = "Точки пересечения:\n"
    for i, point in enumerate(upper_points):
        intersection_text += f"X{i + 1}({point['p']:.3f}, {point['value']:.3f})\n"
    for i, point in enumerate(lower_points):
        intersection_text += f"Y{i + 1}({point['p']:.3f}, {point['value']:.3f})\n"

    # Добавляем текст на график
    plt.figtext(0.02, 0.02, intersection_text, fontsize=9,
                bbox=dict(boxstyle="round,pad=0.5", fc="lightyellow", alpha=0.8))

    # Настраиваем график
    plt.xlabel('Вероятность p (использования Протокола 1)', fontsize=12)
    plt.ylabel('Среднее время передачи', fontsize=12)
    plt.title('Платежные функции с верхней и нижней огибающими', fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=10, loc='upper right')

    # Устанавливаем пределы осей
    plt.xlim(0, 1)

    # Автоматически устанавливаем пределы по Y
    y_min = min(lower_envelope) - 2
    y_max = max(upper_envelope) + 2
    plt.ylim(max(0, y_min), y_max)

    # Отображаем график
    plt.tight_layout()
    #plt.show()

    return functions, intersections, (min_upper_p, min_upper_value), upper_points, lower_points


# Основная программа
payment_matrix = [
    [21, 12, 15, 23, 18],  # Протокол 1
    [11, 33, 28, 16, 19]  # Протокол 2
]

print("Платежная матрица:")
print("       B1  B2  B3  B4  B5")
print(f"A1:   {payment_matrix[0]}")
print(f"A2:   {payment_matrix[1]}")
print()

# Строим графики и получаем информацию о функциях и пересечениях
functions, intersections, minimax_point, upper_points, lower_points = plot_payment_functions_with_envelopes(
    payment_matrix)
# Выводим уравнения платежных функций
print("Уравнения платежных функций:")
for func in functions:
    print(func['equation'])
print()
# Выводим информацию о точках пересечения на огибающих
print("Точки верхней огибающей:")
for i, point in enumerate(upper_points):
    print(f"X{i + 1}: p = {point['p']:.3f}, значение = {point['value']:.3f} (B{point['func1']}∩B{point['func2']})")

print("\nТочки нижней огибающей:")
for i, point in enumerate(lower_points):
    print(f"Y{i + 1}: p = {point['p']:.3f}, значение = {point['value']:.3f} (B{point['func1']}∩B{point['func2']})")
print()
# Выводим информацию о минимаксной точке
print("Минимаксная точка (оптимальная стратегия):")
print(f"Вероятность p = {minimax_point[0]:.4f}")
print(f"Цена игры V = {minimax_point[1]:.4f}")
print(f"Оптимальная смешанная стратегия:")
print(f"  Использовать Протокол 1 с вероятностью {minimax_point[0]:.3f}")
print(f"  Использовать Протокол 2 с вероятностью {1 - minimax_point[0]:.3f}")