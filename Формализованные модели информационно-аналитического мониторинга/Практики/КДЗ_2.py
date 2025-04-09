import numpy as np
import matplotlib.pyplot as plt


# === Генерация допустимых точек (условие f1*f2 >= 5) ===
def generate_feasible_points(N=100):
    """Генерирует N точек, удовлетворяющих условию f1 * f2 >= 5."""
    points = []
    while len(points) < N:
        f1 = np.random.uniform(0, 15)
        f2 = np.random.uniform(0, 15)
        if f1 * f2 >= 5:  # Условие минимизации
            points.append([f1, f2])
    return np.array(points)


# === Шаг 2. Построение полиэдрального конуса доминирования (с динамическим пересчетом векторов) ===
def find_intersection(mu_min, mu_max):
    """Находим точку пересечения прямой L(μ) = 0 с ребрами гиперпараллелепипеда."""

    # Прямая L(μ) = 0: соединение точек (0,1) и (1,0)
    # Линия y = 1 - x (так как проходящая через (0,1) и (1,0))

    intersections = []

    # Пересечение с ребром, где f1 = μ1min
    x_intersect1 = mu_min[0]
    y_intersect1 = 1 - x_intersect1  # y = 1 - x
    if mu_min[1] <= y_intersect1 <= mu_max[1]:
        intersections.append([x_intersect1, y_intersect1])

    # Пересечение с ребром, где f1 = μ1max
    x_intersect2 = mu_max[0]
    y_intersect2 = 1 - x_intersect2  # y = 1 - x
    if mu_min[1] <= y_intersect2 <= mu_max[1]:
        intersections.append([x_intersect2, y_intersect2])

    # Пересечение с ребром, где f2 = μ2min
    y_intersect3 = mu_min[1]
    x_intersect3 = 1 - y_intersect3  # x = 1 - y
    if mu_min[0] <= x_intersect3 <= mu_max[0]:
        intersections.append([x_intersect3, y_intersect3])

    # Пересечение с ребром, где f2 = μ2max
    y_intersect4 = mu_max[1]
    x_intersect4 = 1 - y_intersect4  # x = 1 - y
    if mu_min[0] <= x_intersect4 <= mu_max[0]:
        intersections.append([x_intersect4, y_intersect4])

    return np.array(intersections)


# === Вычисление угла между вектором и осью абсцисс ===
def compute_angle(v):
    """Вычисляет угол между вектором v и осью абсцисс."""
    return np.arctan2(v[1], v[0])  # arctan2 учитывает и знак угла


# === Шаг 3. Проверка попадания точки в полиэдральный конус ===
def is_point_in_cone(F, B):
    """Проверяет, попадает ли точка F в полиэдральный конус, определенный матрицей B."""

    # Вычисляем углы для всех векторов в B
    angles = [compute_angle(b) for b in B]

    # Нахождение минимального и максимального углов
    fi_min = min(angles)
    fi_max = max(angles)

    # Вычисляем угол для точки F
    fi = compute_angle(F)

    # Точка попадает в полиэдральный конус, если угол лежит в пределах [fi_min, fi_max]
    return fi_min <= fi <= fi_max


# === Шаг 4. Проверка доминирования между двумя точками для минимизации ===
def is_dominating(F_i, F_j):
    """Проверяет, доминирует ли точка F_i над точкой F_j в задаче минимизации."""
    return (F_i[0] <= F_j[0] and F_i[1] <= F_j[1]) and (F_i[0] < F_j[0] or F_i[1] < F_j[1])


# === Шаг 5. Нахождение точек, принадлежащих полиэдральному конусу доминирования ===
def find_points_in_cone(fx, B):
    """Находим все точки, которые принадлежат полиэдральному конусу доминирования."""
    points_in_cone = []
    for F in fx:
        if is_point_in_cone(F, B):
            # Проверяем, что точка не доминируется другими точками
            is_efficient = True
            for F_j in fx:
                if F is not F_j and is_dominating(F_j, F):
                    is_efficient = False
                    break
            if is_efficient:
                points_in_cone.append(F)
    return np.array(points_in_cone)


# === Шаг 6. Построение полиэдрального конуса доминирования (с динамическим пересчетом векторов) ===
def construct_polyhedral_cone(mu_min, mu_max):
    """Строим полиэдральный конус доминирования с учетом пересечений прямой L(μ) = 0 и ребер гиперпараллелепипеда."""
    B = []

    # Пересекаем гиперпараллелепипед с прямой L(μ) = 0
    intersections = find_intersection(mu_min, mu_max)

    # Добавляем все пересечения в список B (векторы от (0, 0) к точкам пересечения)
    for point in intersections:
        B.append(point)

    return np.array(B)


# === Отображение графиков ===
def plot_lights_and_optimal_points(fx, pareto, f_omega, B, mu_min, mu_max, case_num):
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # 1-й график: Геометрическое построение конуса доминирования
    axes[0].set_title(f'Геометрическое построение конуса доминирования (Вариант {case_num})')
    axes[0].set_xlabel('f1')
    axes[0].set_ylabel('f2')

    # Рисуем лучи для каждого пересечения
    mem=0
    for b in B:
        if mem == 0:
            axes[0].plot([0, b[0]], [0, b[1]], 'r-', label='Вектора')  # Непрерывные красные линии
            mem +=1
        else:
            axes[0].plot([0, b[0]], [0, b[1]], 'r-')
    # Рисуем прямую L(μ) = 0 (от (0, 1) до (1, 0))
    axes[0].plot([0, 1], [1, 0], 'b-', label='L(μ) = 0')  # Прямая L(μ) = 0 (синий)

    # Рисуем гиперпараллелепипед (прямоугольник с синими линиями)
    axes[0].plot([mu_min[0], mu_max[0]], [mu_min[1], mu_min[1]], 'b-')  # Нижняя граница
    axes[0].plot([mu_min[0], mu_max[0]], [mu_max[1], mu_max[1]], 'b-')  # Верхняя граница
    axes[0].plot([mu_min[0], mu_min[0]], [mu_min[1], mu_max[1]], 'b-')  # Левая граница
    axes[0].plot([mu_max[0], mu_max[0]], [mu_min[1], mu_max[1]], 'b-')  # Правая граница

    # 2-й график: Все точки (черные) и парето-оптимальные точки (зеленые)
    axes[1].scatter(fx[:, 0], fx[:, 1], s=10, alpha=0.3, color='black')
    if pareto.size > 0:
        axes[1].scatter(pareto[:, 0], pareto[:, 1], s=20, color='green')
    axes[1].set_title(f'Все точки и Парето-оптимальные (Вариант {case_num})')
    axes[1].set_xlabel('f1')
    axes[1].set_ylabel('f2')

    # 3-й график: Все точки (черные), парето-оптимальные точки, омега-оптимальные (красные)
    axes[2].scatter(fx[:, 0], fx[:, 1], s=10, alpha=0.3, color='black')
    if pareto.size > 0:
        axes[2].scatter(pareto[:, 0], pareto[:, 1], s=20, color='green')
    if f_omega.size > 0:
        axes[2].scatter(f_omega[:, 0], f_omega[:, 1], s=20, color='red')
    axes[2].set_title(f'Парето и Омега-оптимальные (Вариант {case_num})')
    axes[2].set_xlabel('f1')
    axes[2].set_ylabel('f2')

    for ax in axes:
        ax.grid(True)
        ax.legend()

    plt.tight_layout()
    plt.show()


# === Шаг 7. Основной анализ с учетом пересечений и разбиений области Парето ===
def analyze_all_cases():
    cases = [
        (0.2, 0.6, 0.4, 0.8),
        (0.4, 0.8, 0.2, 0.6),
        (0.3, 0.6, 0.3, 0.6)
    ]

    for N in [10000]:
        print(f"\n==== Анализ для N = {N} ====")
        fx = generate_feasible_points(N)
        pareto = find_points_in_cone(fx,construct_polyhedral_cone([0, 0], [1,1]))  # для парето-оптимальных точек использовать веса 0,1,0,1
        print(f"|F(X)| = {len(fx)}")
        print(f"|Fp(X)| = {len(pareto)}")

        for i, (mu1min, mu1max, mu2min, mu2max) in enumerate(cases):
            B = construct_polyhedral_cone([mu1min, mu2min], [mu1max, mu2max])
            f_omega = find_points_in_cone(fx, B)

            print(f"Кейс {i + 1}: |FΩ(X)| = {len(f_omega)}")

            # Визуализируем результаты
            plot_lights_and_optimal_points(fx, pareto, f_omega, B, [mu1min, mu2min], [mu1max, mu2max], i + 1)


# === Запуск анализа ===
analyze_all_cases()
