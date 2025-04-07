import numpy as np
import matplotlib.pyplot as plt

n = 5
f1min,f1max,f2min,f2max=0,3*n,0,3*n
# === Генерация бинарных кодов Грея ===
def gray_codes(n):
    if n == 0:
        return ['']
    prev = gray_codes(n - 1)
    return ['0' + code for code in prev] + ['1' + code for code in reversed(prev)]


# === Шаг 1. Генерация допустимых точек ===
def generate_feasible_points(N=1000):
    """Генерирует N точек, удовлетворяющих условию f1 * f2 <= 5."""
    points = []
    while len(points) < N:
        f1 = np.random.uniform(f1min, f1max)
        f2 = np.random.uniform(f1min, f2max)
        if f1 * f2 <= n:
            points.append([f1, f2])
    return np.array(points)


# === Шаг 2. Нахождение пересечений с гиперболой f1 * f2 = 5 ===
def find_intersection_with_hyperbola(vector, origin=(0, 0)):
    """
    Для заданного вектора находим точку пересечения с гиперболой f1 * f2 = 5.
    Вектор задается как координаты (dx, dy).
    """
    dx, dy = vector
    if dy == 0 or dx == 0:  # Если вектор параллелен осям
        return None
    x_intersect = np.sqrt(n * dx / dy)  # решаем для x
    y_intersect = (dy / dx) * x_intersect  # решаем для y
    return (x_intersect, y_intersect)


# === Шаг 3. Нахождение угла между двумя векторами ===
def angle_between_vectors(v1, v2):
    """Вычисляет угол между двумя векторами в радианах."""
    dot_product = np.dot(v1, v2)
    norm_v1 = np.linalg.norm(v1)
    norm_v2 = np.linalg.norm(v2)
    cos_theta = dot_product / (norm_v1 * norm_v2)
    cos_theta = np.clip(cos_theta, -1.0, 1.0)  # Для числовой стабильности
    return np.arccos(cos_theta)


# === Шаг 4. Нахождение Парето-оптимальных точек (максимизация) ===
def pareto_front_maximization(points):
    pareto = []
    for i, p in enumerate(points):
        if not any(np.all(q >= p) and np.any(q > p) for j, q in enumerate(points) if j != i):
            pareto.append(p)
    return np.array(pareto)


# === Шаг 5. Построение матрицы B с учетом интервала неопределенности для весов ===
def construct_B(mu_min, mu_max):
    """Строим матрицу B, содержащую векторы, определяющие конус."""
    # В этой матрице будем хранить вектора (направления)
    B = []

    # Генерируем все возможные комбинации для 2D (mu_min и mu_max)
    v1 = np.array([mu_min[0], mu_min[1]])
    v2 = np.array([mu_min[0], mu_max[1]])
    v3 = np.array([mu_max[0], mu_min[1]])
    v4 = np.array([mu_max[0], mu_max[1]])

    # Добавляем все возможные вектора в список B
    B.append(v1)
    B.append(v2)
    B.append(v3)
    B.append(v4)

    return np.array(B)


# === Шаг 6. Нахождение Ω-оптимальных точек с использованием углов ===
def find_omega_optimal_points(fx, B, pareto):
    omega_opt = []

    # Шаг 1: Вычисляем углы для каждого вектора
    angles = []
    for b in B:
        angle = angle_between_vectors(np.array([1, 0]), b)  # угол с осью абсцисс
        angles.append(angle)

    # Шаг 2: Находим минимальный и максимальный углы для конуса
    min_angle = min(angles)
    max_angle = max(angles)

    # Шаг 3: Проверяем, попадает ли угол прямой, идущей из каждой точки, в диапазон углов конуса
    for p in pareto:  # Только по парето-оптимальным точкам
        vector_p = np.array(p)
        angle_p = angle_between_vectors(np.array([1, 0]), vector_p)  # угол с осью абсцисс

        if min_angle <= angle_p <= max_angle:
            omega_opt.append(p)

    return np.array(omega_opt)


# === Шаг 7. Отображение лучей и Ω-оптимальных точек ===
def plot_lights_and_optimal_points(fx, pareto, f_omega, B):
    fig, axes = plt.subplots(1, 1, figsize=(12, 7))

    # График Парето и Ω-оптимальных точек
    axes.scatter(fx[:, 0], fx[:, 1], s=10, alpha=0.3, color='gray', label='F(X)')
    if pareto.size > 0:
        axes.scatter(pareto[:, 0], pareto[:, 1], s=20, color='green', label='Парето-оптимальные')
    if f_omega.size > 0:
        axes.scatter(f_omega[:, 0], f_omega[:, 1], s=20, color='yellow', label='Ω-оптимальные')

    # Добавляем лучи
    for b in B:
        intersection = find_intersection_with_hyperbola(b)
        if intersection:
            axes.plot([0, intersection[0]], [0, intersection[1]], 'r--', label='Лучи')

    axes.set_title(f'Парето и Ω-оптимальные точки')
    axes.set_xlabel('f1')
    axes.set_ylabel('f2')
    axes.legend()
    axes.grid(True)

    plt.tight_layout()
    plt.show()


# === Шаг 8. Основной анализ с учетом пересечений и разбиений области Парето ===
def analyze_all_cases():
    cases = [
        (0.2, 0.6, 0.4, 0.8),
        (0.4, 0.8, 0.2, 0.6),
        (0.3, 0.6, 0.3, 0.6)
    ]

    for N in [100, 1000]:
        print(f"\n==== Анализ для N = {N} ====")
        fx = generate_feasible_points(N)
        pareto = pareto_front_maximization(fx)
        print(f"|F(X)| = {len(fx)}")
        print(f"|Fp(X)| = {len(pareto)}")

        for i, (mu1min, mu1max, mu2min, mu2max) in enumerate(cases):
            B = construct_B([mu1min, mu2min], [mu1max, mu2max])
            f_omega = find_omega_optimal_points(fx, B, pareto)

            print(f"Кейс {i + 1}: |FΩ(X)| = {len(f_omega)}")

            # Визуализируем лучи и Ω-оптимальные точки на одном графике
            plot_lights_and_optimal_points(fx, pareto, f_omega, B)


# === Запуск анализа ===
analyze_all_cases()
