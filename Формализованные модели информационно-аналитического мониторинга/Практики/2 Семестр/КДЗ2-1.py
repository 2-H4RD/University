import matplotlib.pyplot as plt
import numpy as np
from tabulate import tabulate

# Исходная матрица Q (значения f_1 и f_2 для каждого проекта и состояния внешней среды)
Q = [
    [(5, 10), (2, 7), (8, 6), (5, 9)],
    [(4, 4), (5, 7), (9, 6), (4, 4)],
    [(4, 8), (1, 9), (7, 3), (7, 5)],
    [(4, 1), (6, 4), (9, 2), (7, 2)],
    [(1, 3), (3, 5), (4, 2), (3, 3)],
    [(5, 4), (2, 6), (3, 3), (2, 4)],
    [(11, 5), (2, 7), (4, 5), (2, 3)],
    [(4, 3), (3, 7), (10, 4), (3, 8)],
    [(1, 10), (2, 6), (3, 6), (2, 4)],
    [(4, 10), (7, 5), (6, 4), (4, 8)],
    [(8, 7), (9, 7), (3, 2), (5, 3)],
    [(1, 3), (4, 8), (2, 6), (2, 5)],
    [(5, 3), (4, 10), (2, 6), (3, 4)],
    [(2, 9), (3, 6), (3, 12), (4, 8)],
    [(3, 6), (5, 8), (5, 7), (3, 11)],
    [(7, 12), (4, 9), (7, 7), (4, 8)]
]

# Инициализация списков для хранения результатов
min_points_f1 = []
min_points_f2 = []


# Обрабатываем каждый проект
for project in range(len(Q)):
    # Для каждого проекта находим минимальные значения по f_1 и f_2 для каждого состояния среды
    min_values_f1 = []
    min_values_f2 = []

    for state in range(len(Q[project])):
        # Для каждого состояния добавляем минимальные значения f_1 и f_2
        min_values_f1.append(Q[project][state][0])
        min_values_f2.append(Q[project][state][1])

    # Точка максимального пессимизма для f_1 и f_2 (минимум по каждой координате)
    min_f1 = min(min_values_f1)
    min_f2 = min(min_values_f2)

    # Добавляем результат в списки
    min_points_f1.append(min_f1)
    min_points_f2.append(min_f2)


# 1) Вершины и рёбра по Грею
def generate_vertices(mu_min, mu_max):
    return [
        np.array([mu_min[0], mu_min[1]]),  # код 00
        np.array([mu_max[0], mu_min[1]]),  # код 01
        np.array([mu_max[0], mu_max[1]]),  # код 11
        np.array([mu_min[0], mu_max[1]]),  # код 10
    ]


def build_edges():
    return [(0, 1), (1, 2), (2, 3), (3, 0)]


# 2) Пересечение ребра с линией μ1+μ2=1
def intersect_edge(p, q):
    Lp, Lq = p.sum() - 1, q.sum() - 1
    if Lp * Lq > 0:
        return None
    # вертикальное ребро?
    if np.isclose(p[0], q[0]):
        x = p[0];
        y = 1 - x
    else:
        y = p[1];
        x = 1 - y
    return np.array([x, y])


# 3) Построение матрицы B для заданного интервала весов
def construct_polyhedral_cone(mu_min, mu_max):
    if np.allclose(mu_min, mu_max):
        return np.array([mu_min], dtype=float)
    verts = generate_vertices(mu_min, mu_max)
    B = []
    for i, j in build_edges():
        P = intersect_edge(verts[i], verts[j])
        if P is None: continue
        if mu_min[0] <= P[0] <= mu_max[0] and mu_min[1] <= P[1] <= mu_max[1]:
            B.append(P)
    return np.unique(np.array(B), axis=0) if B else np.empty((0, 2))


# 4) Проверка: Fi доминируется Fj по конусу B? (для максимизации)
def is_dominated_by(Fi, Fj, B,type):
    if B.size == 0:
        return False
    if type == 'max':
        diff = Fi - Fj  # для максимизации
        ge = [np.dot(b, diff) <= 0 for b in B]  # знак неравенства изменился на <= для максимизации
        gt = [np.dot(b, diff) < 0 for b in B]  # строгое неравенство для максимизации
        return all(ge) and any(gt)
    if type == 'min':
        diff = Fi - Fj  # для максимизации
        ge = [np.dot(b, diff) >= 0 for b in B]  # знак неравенства изменился на >= для минимизации
        gt = [np.dot(b, diff) > 0 for b in B]  # строгое неравенство для минимизации
        return all(ge) and any(gt)


# 5) Однократное построение парето через B0 = B([0,0],[1,1])
def build_pareto(fx, type):
    B0 = construct_polyhedral_cone([0, 0], [1, 1])
    pareto = []
    for Fi in fx:
        if not any(is_dominated_by(Fi, Fj, B0,type) for Fj in fx if not np.allclose(Fi, Fj)):
            pareto.append(Fi)
    return np.array(pareto)

def calculate_ideal_point(Q,column):
    f1_max,f2_max = 0,0
    for i in range (len(Q)):
        if f1_max <= Q[i][column][0]:
            f1_max = Q[i][column][0]
        if f2_max <= Q[i][column][1]:
            f2_max = Q[i][column][1]
    return f1_max,f2_max

def build_regret_matrix(Q):
    regret_matrix = [[list(state) for state in project] for project in Q]
    for i in range (len(Q)):
        for j in range(len(Q[i])):
            ideal_point = list(calculate_ideal_point(Q,j))
            regret_matrix[i][j][0]=ideal_point[0]-Q[i][j][0]
            regret_matrix[i][j][1] = ideal_point[1] - Q[i][j][1]
    return np.array(regret_matrix)

def build_ideal_points_for_projects(regret_matrix):
    ideal_points = []
    for regret_row in regret_matrix:
        ideal_point_project = np.max(regret_row, axis=0)  # Для каждого проекта находим максимум среди состояний
        ideal_points.append(ideal_point_project)
    return np.array(ideal_points)

# Строим множество Парето
pareto_points = build_pareto(np.column_stack((min_points_f1, min_points_f2)), type='max')


# 6) Поиск оптимальной точки, сравнивая минимумы по каждой компоненте
def find_optimal_solution(pareto_points):
    best_solution = None
    max_min_value = -float('inf')

    for point in pareto_points:
        min_value = min(point[0], point[1])  # минимальная компонента
        if min_value > max_min_value:
            max_min_value = min_value
            best_solution = point

    return best_solution


# 1) Принцип Вальда
def valda_criterion(f_values):
    min_f_values = np.min(f_values, axis=1)  # Находим минимальное значение f1 для каждого проекта
    max_min_f = np.max(min_f_values)  # Максимальное минимальное значение f1
    optimal_projects = np.where(min_f_values == max_min_f)[0]  # Находим все проекты, которые соответствуют максимальному минимальному f1
    return optimal_projects, min_f_values[optimal_projects]

# 2) Принцип Сэвиджа
def savage_criterion(f_values):
    ideal_f = np.max(f_values, axis=0)  # Находим идеальные значения для f1 по каждому состоянию
    regret_matrix = ideal_f - f_values  # Строим матрицу сожалений (разница между идеальной и текущей точкой)
    regret_values = np.max(regret_matrix, axis=1)  # Находим максимальное сожаление для каждого проекта
    min_regret = np.min(regret_values)  # Минимальное сожаление
    optimal_projects = np.where(regret_values == min_regret)[0]  # Находим все проекты с минимальным сожалением
    return optimal_projects, regret_values[optimal_projects]

# 3) Принцип Гурвица
def hurwicz_criterion(f_values, alpha=0.5):
    hurwicz_values = []
    for f in f_values:
        hurwicz_value = alpha * np.max(f) + (1 - alpha) * np.min(f)  # Применяем формулу Гурвица
        hurwicz_values.append(hurwicz_value)
    hurwicz_values = np.array(hurwicz_values)  # Преобразуем список в массив
    max_hurwicz_value = np.max(hurwicz_values)  # Максимальное значение
    optimal_projects = np.where(hurwicz_values == max_hurwicz_value)[0]  # Находим все проекты с максимальным значением
    return optimal_projects, hurwicz_values[optimal_projects]

# 4) Принцип Лапласа
def laplace_criterion(f_values):
    laplace_values = np.mean(f_values, axis=1)  # Среднее значение f1 по всем состояниям
    max_laplace_value = np.max(laplace_values)  # Максимальное среднее значение
    optimal_projects = np.where(laplace_values == max_laplace_value)[0]  # Находим все проекты с максимальным средним значением
    return optimal_projects, laplace_values[optimal_projects]

#-------------------------ЗАДНАИЕ1-----------------------------------------------------------

# Найдем оптимальную точку
optimal_point = find_optimal_solution(pareto_points)


#График с оптимальной точкой по критерию векторного максимина
plt.figure(figsize=(8, 6))  # Устанавливаем размер графика

# Подписываем каждую точку рядом с графиком
x_offset = 1.2  # Смещение по оси X для текста
y_offset = 0.05  # Смещение по оси Y для текста

# Печатаем подписи рядом с графиком
for i in range(len(min_points_f1)):
    plt.figtext(0.91, 0.93 - (i + 1) * y_offset, f"X{i + 1} ({min_points_f1[i]}, {min_points_f2[i]})", ha='left',
                va='top', fontsize=9)
    if min_points_f1[i] == optimal_point[0] and min_points_f2[i] == optimal_point[1]:
        solution_pont_mimnax = i
# Рисуем все точки чёрным цветом
plt.scatter(min_points_f1, min_points_f2, color='black', marker='o', label="Все точки")

# Рисуем только Парето-оптимальные точки зелёным
plt.scatter(pareto_points[:, 0], pareto_points[:, 1], color='green', marker='o', label="Парето-оптимальные точки")

# Выделяем оптимальную точку как красную точку
plt.scatter(optimal_point[0], optimal_point[1], color='red', marker='o', label="Оптимальная точка")

# Настройки графика
plt.xlabel('f1')  # Подпись оси x
plt.ylabel('f2')  # Подпись оси y
plt.title('График распределения точек крайнего пессимизма')

# Показать сетку
plt.grid(True)
plt.legend()
plt.show()

#-------------------------ЗАДНАИЕ2-----------------------------------------------------------

# Строим матрицу сожалений
regret_matrix = build_regret_matrix(Q)


# Строим идеальные точки для каждого проекта
ideal_points_for_projects = build_ideal_points_for_projects(regret_matrix)

# Построение полиэдрального конуса и нахождение Парето-оптимальных точек
pareto_points = build_pareto(ideal_points_for_projects, type = 'min')

# Поиск оптимальной точки из множества Парето-оптимальных
optimal_point = find_optimal_solution(pareto_points)

# Оптимальная точка для по критерияю минимаксного сожаления
plt.figure(figsize=(8, 6))  # Устанавливаем размер графика

# Рисуем все точки чёрным цветом
plt.scatter(ideal_points_for_projects[:, 0], ideal_points_for_projects[:, 1], color='black', marker='o', label="Все точки")

# Рисуем Парето-оптимальные точки зелёным
plt.scatter(pareto_points[:, 0], pareto_points[:, 1], color='green', marker='o', label="Парето-оптимальные точки")

# Выделяем оптимальную точку как красную точку
plt.scatter(optimal_point[0], optimal_point[1], color='red', marker='o', label="Оптимальная точка")

# Добавляем подписи к точкам
x_offset = 1.2  # Смещение по оси X для текста
y_offset = 0.05  # Смещение по оси Y для текста

# Подпись для всех точек
for i, point in enumerate(ideal_points_for_projects):
    plt.figtext(0.91, 0.93 - (i + 1) * y_offset, f"X{i + 1} ({point[0]}, {point[1]})", ha='left', va='top', fontsize=9)
    if point[0] == optimal_point[0] and point[1] == optimal_point[1]:
        solution_pont_maxmin = i
# Настройки графика
plt.xlabel('f1')  # Подпись оси x
plt.ylabel('f2')  # Подпись оси y
plt.title('График распределения точек минимаксного сожаления')

# Показать сетку
plt.grid(True)
plt.legend()
plt.show()

#-------------------------ЗАДНАИЕ3-----------------------------------------------------------
# Извлекаем только f1 значения из матрицы Q для дальнейшего анализа
f1_values = np.array([[project[0] for project in row] for row in Q])

# Применяем принципы
optimal_project_valda_f1, valda_value = valda_criterion(f1_values)
optimal_project_savage_f1, savage_value = savage_criterion(f1_values)
optimal_project_hurwicz_f1, hurwicz_value = hurwicz_criterion(f1_values, alpha=0.5)
optimal_project_laplace_f1, laplace_value = laplace_criterion(f1_values)

# Выводим оптимальные проекты по каждому критерию
print(f"Оптимальный проект по принципу Вальда для f1: X{optimal_project_valda_f1 + 1}, f1 = {valda_value}")
print(f"Оптимальный проект по принципу Сэвиджа для f1: X{optimal_project_savage_f1 + 1}, f1 = {savage_value}")
print(f"Оптимальный проект по принципу Гурвица (α=0.5) для f1: X{optimal_project_hurwicz_f1 + 1}, f1 = {hurwicz_value}")
print(f"Оптимальный проект по принципу Лапласа для f1:: X{optimal_project_laplace_f1 + 1}, f1 = {laplace_value} \n")

#-------------------------ЗАДНАИЕ4-----------------------------------------------------------

# Извлекаем только f2 значения из матрицы Q для дальнейшего анализа
f2_values = np.array([[project[1] for project in row] for row in Q])

# Применяем принципы
optimal_project_valda_f2, valda_value = valda_criterion(f2_values)
optimal_project_savage_f2, savage_value = savage_criterion(f2_values)
optimal_project_hurwicz_f2, hurwicz_value = hurwicz_criterion(f2_values, alpha=0.5)
optimal_project_laplace_f2, laplace_value = laplace_criterion(f2_values)

# Выводим оптимальные проекты по каждому критерию
print(f"Оптимальный проект по принципу Вальда для f2: X{optimal_project_valda_f2 + 1}, f2 = {valda_value}")
print(f"Оптимальный проект по принципу Сэвиджа для f2: X{optimal_project_savage_f2 + 1}, f2 = {savage_value}")
print(f"Оптимальный проект по принципу Гурвица (α=0.5) для f2: X{optimal_project_hurwicz_f2 + 1}, f2 = {hurwicz_value}")
print(f"Оптимальный проект по принципу Лапласа для f2: X{optimal_project_laplace_f2 + 1}, f2 = {laplace_value} \n")

#-------------------------МАТРИЦА ГОЛОСОВАНИЯ-----------------------------------------------------------
voting_matrix = np.zeros((len(Q), 11), dtype=int)
max_total = 0
print(len(Q))
for i in range (len(Q)):
    total = 0
    if i == solution_pont_mimnax:
        voting_matrix[i][0] = 1
        total += 1
    if i== solution_pont_maxmin:
        voting_matrix[i][1] = 1
        total += 1
    if i in optimal_project_valda_f1:
        voting_matrix[i][2] = 1
        total += 1
    if i in optimal_project_savage_f1:
        voting_matrix[i][3] = 1
        total += 1
    if i in optimal_project_hurwicz_f1:
        voting_matrix[i][4] = 1
        total += 1
    if i in optimal_project_laplace_f1:
        voting_matrix[i][5] = 1
        total += 1
    if i in optimal_project_valda_f2:
        voting_matrix[i][6] = 1
        total += 1
    if i in optimal_project_savage_f2:
        voting_matrix[i][7] = 1
        total += 1
    if i in optimal_project_hurwicz_f2:
        voting_matrix[i][8] = 1
        total += 1
    if i in optimal_project_laplace_f2:
        voting_matrix[i][9] = 1
        total += 1
    voting_matrix[i][10] = total
    if max_total <= total:
        max_total = total
# Формируем заголовки столбцов
headers = [
    "ВекторМаксМин.f1", "ВекторМинМакс.f1","Вальд.f1", "Сэвидж.f1", "Гурвиц.f1", "Лапл.f1",
    "Вальд.f2", "Сэвидж.f2", "Гурвиц.f2", "Лапл.f2", "Итог"
]

# Преобразуем матрицу голосования в формат для `tabulate`
table = []
for i, row in enumerate(voting_matrix):
    row_data = row.tolist()  # Преобразуем строку в список
    table.append([f"X{i+1}"] + row_data)  # Добавляем индекс проекта

# Выводим таблицу с результатами
print("Матрица голосования:")
print(tabulate(table, headers=["Проект"] + headers, tablefmt="grid"))

# Выводим итоговый проект
max_votes = np.max(voting_matrix[:, 10])
optimal_projects_final = np.where(voting_matrix[:, 10] == max_votes)[0]
optimal_projects_final = ', '.join([f"X{x+1}" for x in optimal_projects_final])
print(f"\nСамые оптимальные проекты по итогам голосования: {optimal_projects_final}")
