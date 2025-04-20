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
def construct_polyhedral_cone(mu_min, mu_max):
    """Строим полиэдральный конус доминирования с учетом интервала неопределенности для весов."""
    B = []

    # Генерация всех возможных векторов (ребер) полиэдра, которые зависят от весов
    v1 = np.array([mu_min[0], mu_min[1]])  # Нижняя левая точка (критерии f1 и f2 минимальны)
    v2 = np.array([mu_min[0], mu_max[1]])  # Верхняя левая точка (f1 минимален, f2 максимален)
    v3 = np.array([mu_max[0], mu_min[1]])  # Нижняя правая точка (f1 максимален, f2 минимален)
    v4 = np.array([mu_max[0], mu_max[1]])  # Верхняя правая точка (f1 и f2 максимальны)

    # Добавляем все возможные вектора в список B
    B.append(v1)
    B.append(v2)
    B.append(v3)
    B.append(v4)

    # Убираем дублирующиеся строки в матрице B
    B = np.unique(B, axis=0)

    return B


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


# === Отображение графиков ===
def plot_polyhedral_cone(fx, points_in_cone, B):
    fig, ax = plt.subplots(figsize=(10, 6))

    # Рисуем все точки (черные)
    ax.scatter(fx[:, 0], fx[:, 1], s=10, alpha=0.3, color='black', label='Все точки')

    # Рисуем полиэдральный конус (границы)
    for b in B:
        ax.plot([0, b[0]], [0, b[1]], 'r-', label='Границы конуса')  # Непрерывные красные линии

    # Рисуем точки, которые попадают в полиэдральный конус и доминирующие (красные)
    if points_in_cone.size > 0:
        ax.scatter(points_in_cone[:, 0], points_in_cone[:, 1], s=20, color='red', label='Точки в конусе')

    ax.set_title('Полиэдральный конус доминирования')
    ax.set_xlabel('f1')
    ax.set_ylabel('f2')
    ax.grid(True)
    ax.legend()
    plt.show()


# === Основной тестовый процесс ===
def run_test(mu_min, mu_max, N=100):
    # Генерация случайных точек
    fx = generate_feasible_points(N)

    # Построение полиэдрального конуса
    B = construct_polyhedral_cone(mu_min, mu_max)

    # Нахождение точек, принадлежащих полиэдральному конусу
    points_in_cone = find_points_in_cone(fx, B)

    # Отображение результатов
    plot_polyhedral_cone(fx, points_in_cone, B)


# Тестирование с различными весами
mu_min_1 = [0, 0]  # f1 и f2 равны
mu_max_1 = [1, 1]  # f1 и f2 равны

mu_min_2 = [0.8, 0.2]  # f1 более важен
mu_max_2 = [1, 1]  # f2 немного менее важен

mu_min_3 = [0, 0.8]  # f2 более важен
mu_max_3 = [1, 1]  # f1 менее важен

# Пример с различными весами
run_test(mu_min_1, mu_max_1)  # f1 и f2 равны
run_test(mu_min_2, mu_max_2)  # f1 более важен
run_test(mu_min_3, mu_max_3)  # f2 более важен
