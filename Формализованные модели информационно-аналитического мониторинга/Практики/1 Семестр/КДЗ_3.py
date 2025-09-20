import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog
from scipy.spatial import ConvexHull

# Матрица коэффициентов для ограничений
A = np.array([[1, 1], [1, -1], [-3, 2], [1, 0], [1, 0], [0, 1],[0, 1]])  # Для ограничений: x1 + x2 >= 10, x1 - x2 <= 5, -3x1 + 2x2 <= 10
b = np.array([10, 5, 10, 0, 20, 0, 15])  # Правая часть для ограничений
bounds = [(0, 20), (0, 15)]  # Ограничения для x1 и x2


# Проверка, лежит ли точка в области допустимых значений
def satisfies_constraints(x, y):
    if x + y >= 10 and x - y <= 5 and -3 * x + 2 * y <= 10 and 0 <= x <= 20 and 0 <= y <= 15:
        return True
    else:
        return False


# Функция для нахождения пересечений прямых
def find_intersections():
    vertices = []

    # Перебираем все возможные пары прямых
    for i in range(len(A) - 1):
        for j in range(i + 1, len(A)):
            c = np.zeros(2)  # Мы не минимизируем функцию, поэтому c = [0, 0]
            A_ = np.array([A[i], A[j]])  # Коэффициенты для двух ограничений
            b_ = np.array([b[i], b[j]])  # Правая часть для этих двух ограничений
            result = linprog(c, A_eq=A_, b_eq=b_, bounds=bounds, method='highs')
            if result.success:
                x, y = result.x
                if satisfies_constraints(x, y):  # Проверка на удовлетворение ограничениям
                    if [x, y] not in vertices:  # Проверка на уникальность точек
                        vertices.append([x, y])

    return vertices


# Найдем все пересечения
vertices = find_intersections()

# Проверка на пустой список
if len(vertices) < 3:
    raise ValueError("Недостаточно точек пересечения для построения многоугольника.")

# Преобразование списка точек в массив NumPy
vertices = np.array(vertices)

# Используем ConvexHull для сортировки точек по часовой стрелке (или против часовой стрелки)
hull = ConvexHull(vertices)
sorted_vertices = vertices[hull.vertices]

# Построение графика
plt.figure(figsize=(8, 6))

# Добавляем линии ограничений
x_vals = np.linspace(0, 20, 400)
plt.plot(x_vals, 10 - x_vals, label=r"$x_1 + x_2 = 10$", color='r')  # x1 + x2 = 10
plt.plot(x_vals, x_vals - 5, label=r"$x_1 - x_2 = 5$", color='g')  # x1 - x2 = 5
plt.plot(x_vals, (10 + 3 * x_vals) / 2, label=r"$-3x_1 + 2x_2 = 10$", color='b')  # -3x1 + 2x2 = 10

# Ограничения для x1 и x2
plt.axvline(x=0, color='k', linewidth=1)
plt.axvline(x=20, color='k', linewidth=1)
plt.axhline(y=0, color='k', linewidth=1)
plt.axhline(y=15, color='k', linewidth=1)

# Закрашиваем область допустимых решений
polygon = plt.Polygon(sorted_vertices, closed=True, color='lightblue', alpha=0.5)
plt.gca().add_patch(polygon)

# Обозначаем вершины
for vert in sorted_vertices:
    plt.scatter(vert[0], vert[1], color='black', zorder=5)
    plt.text(vert[0], vert[1], f"({vert[0]:.2f}, {vert[1]:.2f})", fontsize=9, ha='center')

# Оформляем график
plt.xlim([0, 20])
plt.ylim([0, 15])
plt.xlabel(r"$x_1$")
plt.ylabel(r"$x_2$")
plt.title("График задачи многокритериальной оптимизации")

plt.grid(True)
plt.legend()
plt.show()
