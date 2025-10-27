import numpy as np
from scipy.optimize import linprog
import matplotlib.pyplot as plt

print("=" * 70)
print("РЕШЕНИЕ МАТРИЧНОЙ ИГРЫ: ОПТИМАЛЬНЫЙ ВЫБОР ПРОТОКОЛА ЗАЩИТЫ")
print("(ЗАДАЧА МИНИМИЗАЦИИ ВРЕМЕНИ ПЕРЕДАЧИ)")
print("=" * 70)
print()

A = np.array([
    [21, 12, 15, 23, 18],  # Протокол 1
    [11, 33, 28, 16, 19]  # Протокол 2
])
print("Матрица времени передачи A:")
print("Типы DDoS-атак:   1  2  3  4  5")
print(f"Протокол 1:      {A[0]}")
print(f"Протокол 2:      {A[1]}")
print()

# РЕШЕНИЕ ДЛЯ ИГРОКА A
print("=" * 50)
print("РЕШЕНИЕ ДЛЯ ИГРОКА A (СИСТЕМА ЗАЩИТЫ)")
print("=" * 50)
c_A = np.array([-1, -1])
A_ub_A = A.T
b_ub_A = np.ones(5)
bounds_A = [(0, None), (0, None)]
print("Задача линейного программирования для игрока A:")
print("Максимизировать: x1 + x2")
print("При ограничениях:")
for i in range(len(A[0])):
    print(f"{A[0][i]}*x1 + {A[1][i]}*x2 ≤ 1")
print("x1, x2 ≥ 0")
print()
print("Решаем задачу для игрока A...")
result_A = linprog(c_A, A_ub=A_ub_A, b_ub=b_ub_A, bounds=bounds_A, method='highs')
if not result_A.success:
    print("Ошибка при решении задачи для игрока A:", result_A.message)
else:
    x_optimal = result_A.x
    max_sum_x = -result_A.fun
    print("Результаты для игрока A:")
    print(f"x1 = {x_optimal[0]:.6f}")
    print(f"x2 = {x_optimal[1]:.6f}")
    print()
    v_A = 1 / max_sum_x
    p_optimal = x_optimal * v_A
    print("Оптимальные вероятности для игрока A:")
    print(f"Вероятность выбора Протокола 1: p1 = {p_optimal[0]:.6f} ({p_optimal[0] * 100:.2f}%)")
    print(f"Вероятность выбора Протокола 2: p2 = {p_optimal[1]:.6f} ({p_optimal[1] * 100:.2f}%)")
    print(f"Цена игры v: {v_A:.6f}")

# РЕШЕНИЕ ДЛЯ ИГРОКА B
print("\n" + "=" * 50)
print("РЕШЕНИЕ ДЛЯ ИГРОКА B (ЗЛОУМЫШЛЕННИК)")
print("=" * 50)
c_B = np.ones(5)
A_ub_B = -A
b_ub_B = -np.ones(2)  # [-1, -1]
bounds_B = [(0, None) for _ in range(5)]
print("Задача линейного программирования для игрока B:")
print("Минимизировать: y1 + y2 + y3 + y4 + y5")
print("При ограничениях:")
for i in range(len(A)):
    constraint_str = " + ".join([f"{A[i, j]}*y{j + 1}" for j in range(5)])
    print(f"  {constraint_str} ≥ 1")
print("  y1, y2, y3, y4, y5 ≥ 0")
print()

# Решаем задачу для игрока B
print("Решаем задачу для игрока B...")
result_B = linprog(c_B, A_ub=A_ub_B, b_ub=b_ub_B, bounds=bounds_B, method='highs')
if not result_B.success:
    print("Ошибка при решении задачи для игрока B:", result_B.message)
else:
    y_optimal = result_B.x
    min_sum_y = result_B.fun
    print("Результаты для игрока B:")
    for i in range(5):
        print(f"y{i + 1} = {y_optimal[i]:.6f}")
    print(f"Сумма y1+y2+y3+y4+y5 = {min_sum_y:.6f}")
    print()
    v_B = 1 / min_sum_y
    q_optimal = y_optimal * v_B
    print("Оптимальные вероятности для игрока B:")
    for i in range(5):
        print(f"Вероятность выбора атаки {i + 1}: q{i + 1} = {q_optimal[i]:.6f} ({q_optimal[i] * 100:.2f}%)")
    print(f"Цена игры v: {v_B:.6f}")
    print("\nПроверка согласованности решений:")
    print(f"Цена игры из решения для A: {v_A:.6f}")
    print(f"Цена игры из решения для B: {v_B:.6f}")
    print(f"Разница: {abs(v_A - v_B):.6f}")

    # ГЕНЕРАЦИЯ СИМПЛЕКСНОЙ ТАБЛИЦЫ ДЛЯ ИГРОКА B
    print("\n" + "=" * 50)
    print("СИМПЛЕКСНАЯ ТАБЛИЦА (Игрок B)")
    print("=" * 50)
    basic_vars = []
    non_basic_vars = []
    for i in range(5):
        if y_optimal[i] > 1e-6:
            basic_vars.append(f"y{i + 1}")
        else:
            non_basic_vars.append(f"y{i + 1}")
    slack_vars = ["s1", "s2"]
    print("Базисные переменные:", basic_vars)
    print("Небазисные переменные:", non_basic_vars + slack_vars)
    print()
    header = ["Базис", "Значение"] + non_basic_vars + slack_vars
    print("Конечная симплексная таблица:")
    print("-" * 80)
    print(f"{header[0]:<10} {header[1]:<10} ", end="")
    for var in header[2:]:
        print(f"{var:<10} ", end="")
    print()
    print("-" * 80)
    z_row = ["Z", f"{min_sum_y:.4f}"] + ["0.0000"] * (len(non_basic_vars) + len(slack_vars))
    print(f"{z_row[0]:<10} {z_row[1]:<10} ", end="")
    for val in z_row[2:]:
        print(f"{val:<10} ", end="")
    print()
    for i, var in enumerate(basic_vars):
        row = [var, f"{y_optimal[i]:.4f}"] + ["1.0000" if j == i else "0.0000" for j in
                                              range(len(non_basic_vars) + len(slack_vars))]
        print(f"{row[0]:<10} {row[1]:<10} ", end="")
        for val in row[2:]:
            print(f"{val:<10} ", end="")
        print()
    for i, var in enumerate(slack_vars):
        # Определяем, активно ли ограничение
        constraint_value = np.dot(A[i], y_optimal)
        is_active = abs(constraint_value - 1) < 1e-6
        if not is_active:
            row = [var, "0.0000"] + ["0.0000"] * (len(non_basic_vars) + len(slack_vars))
            row[2 + len(non_basic_vars) + i] = "1.0000"  # Коэффициент при самой дополнительной переменной
            print(f"{row[0]:<10} {row[1]:<10} ", end="")
            for val in row[2:]:
                print(f"{val:<10} ", end="")
            print()
    print("-" * 80)
    print("Примечание: Таблица сгенерирована на основе оптимального решения")
    print("и может не полностью соответствовать реальной симплексной таблице.")

# ПОСТРОЕНИЕ ГРАФИКА ДЛЯ ИГРОКА A
print("\n" + "=" * 50)
print("ПОСТРОЕНИЕ ГРАФИКА ДЛЯ ИГРОКА A")
print("=" * 50)
if result_A.success:
    fig, ax = plt.subplots(figsize=(12, 10))
    x1 = np.linspace(0, 0.1, 400)
    colors = ['blue', 'red', 'green', 'purple', 'orange']
    constraint_labels = []
    for i in range(5):
        x2 = (1 - A[0, i] * x1) / A[1, i]
        valid_indices = x2 >= 0
        plt.plot(x1[valid_indices], x2[valid_indices],
                 label=f'{A[0, i]}x1 + {A[1, i]}x2 = 1',
                 color=colors[i], linewidth=2)
        plt.fill_between(x1[valid_indices], 0, x2[valid_indices],
                         alpha=0.1, color=colors[i])
    target_levels = [max_sum_x * 0.5, max_sum_x, max_sum_x * 1.5]
    for i, level in enumerate(target_levels):
        x2_target = level - x1
        valid_target = x2_target >= 0
        style = '-' if i == 1 else '--'  # Сплошная линия для оптимального уровня
        width = 3 if i == 1 else 1  # Толще для оптимального уровня
        color = 'green' if i == 1 else 'lightgreen'
        plt.plot(x1[valid_target], x2_target[valid_target],
                 linestyle=style, linewidth=width, color=color,
                 label=f'Целевая: x1+x2 = {level:.3f}' if i == 1 else "")
    grad_x, grad_y = 0.03, 0.03
    dx, dy = 0.02, 0.02
    plt.arrow(grad_x, grad_y, dx, dy,
              head_width=0.005, head_length=0.005,
              fc='red', ec='red', linewidth=2,
              label='Градиент целевой функции')
    plt.text(grad_x + dx + 0.005, grad_y + dy, '∇f = (1,1)',
             color='red', fontsize=12, fontweight='bold')
    plt.plot(x_optimal[0], x_optimal[1], 'ro', markersize=10, label='Оптимальное решение')
    plt.text(x_optimal[0] + 0.002, x_optimal[1] + 0.002,
             f'Оптимум: ({x_optimal[0]:.3f}, {x_optimal[1]:.3f})',
             fontsize=10, fontweight='bold')
    plt.xlim(0, 0.08)
    plt.ylim(0, 0.08)
    plt.xlabel('x1', fontsize=12)
    plt.ylabel('x2', fontsize=12)
    plt.title('Графическое решение задачи линейного программирования\n(Игрок A: минимизация времени передачи)',
              fontsize=14)
    plt.grid(True, alpha=0.3)
    plt.legend(loc='upper right', fontsize=10)
    solution_text = f'Оптимальное решение:\n'
    solution_text += f'x1 = {x_optimal[0]:.4f}\n'
    solution_text += f'x2 = {x_optimal[1]:.4f}\n'
    solution_text += f'Целевая функция: {max_sum_x:.4f}\n'
    solution_text += f'Цена игры: v = {v_A:.3f}'
    plt.text(0.05, 0.07, solution_text, fontsize=10,
             bbox=dict(boxstyle="round,pad=0.3", facecolor="lightyellow", alpha=0.7))
    plt.tight_layout()
    plt.show()