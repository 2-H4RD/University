import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from scipy.optimize import linprog
from itertools import combinations
from numpy.linalg import solve

# Параметры задачи
n = 5
delta_f1 = 2
delta_f2 = 1

# Матрица ограничений (левая часть Ax ≤ b)
A = np.array([
    [1, 2],       # x1 + 2x2 ≤ 20
    [-2, -1],     # -2x1 - x2 ≤ -5
    [-1, 0],      # -x1 ≤ 0
    [1, 0],       # x1 ≤ 10
    [0, -1],      # -x2 ≤ 0
    [0, 1]        # x2 ≤ 7.5
])

b = np.array([
    4 * n,        # 20
    -n,           # -5
    0,            # 0
    2 * n,        # 10
    0,            # 0
    1.5 * n       # 7.5
])

#Поиск вершин многоугольника ОДЗ
vertices = []
for c1, c2 in combinations(range(len(A)), 2):
    A_eq = np.array([A[c1], A[c2]])
    b_eq = np.array([b[c1], b[c2]])
    if np.linalg.matrix_rank(A_eq) == 2:
        try:
            point = solve(A_eq, b_eq)
            if all(np.dot(A, point) <= b + 1e-5):
                vertices.append(tuple(point))
        except np.linalg.LinAlgError:
            continue

# Удаляем дубликаты и сортируем по полярному углу
vertices = list(set(vertices))
center = np.mean(vertices, axis=0)
vertices.sort(key=lambda p: np.arctan2(p[1]-center[1], p[0]-center[0]))

# Параметры для графиков
x1_vals = np.linspace(0, 2 * n + 1, 100)

# 1-й график: ОДЗ и ограничения
plt.figure(figsize=(8, 6))
poly = Polygon(vertices)
x, y = poly.exterior.xy
plt.plot(x, y, 'k-', linewidth=2, label='ОДЗ')

# x1 + 2x2 = 20
x2_vals1 = (4 * n - x1_vals) / 2
plt.plot(x1_vals, x2_vals1, 'blue', linewidth=2, label=r'$x_1 + 2x_2 = 20$')

# 2x1 + x2 = 5
x2_vals2 = n - 2 * x1_vals
plt.plot(x1_vals, x2_vals2, 'orange', linewidth=2, label=r'$2x_1 + x_2 = 5$')

# Метод последовательных уступок

# 1. Максимизируем f1 = x1 + x2
c1 = [-1, -1]
res1 = linprog(c1, A_ub=A, b_ub=b)
opt1 = res1.x
f1_max = -res1.fun
f1_limit = f1_max - delta_f1
print(f"f1 max = {f1_max:.3f} в точке ({opt1[0]:.3f}, {opt1[1]:.3f})")

# Уступка по f1: -x1 - x2 ≤ -(f1_max - delta_f1)
A2 = np.vstack([A, [-1, -1]])
b2 = np.append(b, -f1_limit)

# 2. Максимизируем f2 = -3x1 + x2
c2 = [3, -1]
res2 = linprog(c2, A_ub=A2, b_ub=b2)
opt2 = res2.x
f2_max = -res2.fun
f2_limit = f2_max - delta_f2
print(f"f2 max = {f2_max:.3f} в точке ({opt2[0]:.3f}, {opt2[1]:.3f})")

# Уступка по f2: 3x1 - x2 ≤ -(f2_max - delta_f2)
A3 = np.vstack([A2, [3, -1]])
b3 = np.append(b2, -f2_limit)

# 3. Максимизируем f3 = x1 - 3x2
c3 = [-1, 3]
res3 = linprog(c3, A_ub=A3, b_ub=b3)
opt3 = res3.x
print(f"f3 max = {-res3.fun:.3f} в точке ({opt3[0]:.3f}, {opt3[1]:.3f})")

plt.xlabel(r'$x_1$')
plt.ylabel(r'$x_2$')
plt.title('ОДЗ и метод уступок (первый график)')
plt.grid(True)
plt.legend()
plt.gca().set_aspect('equal', adjustable='box')
plt.xlim(0, 2 * n + 1)
plt.ylim(0, 1.5 * n + 1)
plt.show()

# 2-й график: с ограничением после уступки f1
plt.figure(figsize=(8, 6))
plt.plot(x, y, 'k-', linewidth=2, label='ОДЗ')
plt.plot(x1_vals, x2_vals1, 'blue', linewidth=2, label=r'$x_1 + 2x_2 = 20$')
plt.plot(x1_vals, x2_vals2, 'orange', linewidth=2, label=r'$2x_1 + x_2 = 5$')

# Прямая после уступки f1
x2_vals_f1 = f1_limit - x1_vals
plt.plot(x1_vals, x2_vals_f1, 'magenta', linewidth=2, label=fr'$x_2 = {f1_limit:.1f}- x_1$ (уступка f1)')

plt.xlabel(r'$x_1$')
plt.ylabel(r'$x_2$')
plt.title('После уступки f1 (второй график)')
plt.grid(True)
plt.legend()
plt.gca().set_aspect('equal', adjustable='box')
plt.xlim(0, 2 * n + 1)
plt.ylim(0, 1.5 * n + 1)
plt.show()

# 3-й график: добавляем уступку после f2
plt.figure(figsize=(8, 6))
plt.plot(x, y, 'k-', linewidth=2, label='ОДЗ')
plt.plot(x1_vals, x2_vals1, 'blue', linewidth=2, label=r'$x_1 + 2x_2 = 20$')
plt.plot(x1_vals, x2_vals2, 'orange', linewidth=2, label=r'$2x_1 + x_2 = 5$')

# Прямая после уступки f1
plt.plot(x1_vals, x2_vals_f1, 'magenta', linewidth=2, label=fr'$x_2 = {f1_limit:.1f}- x_1$ (уступка f1)')

# Прямая после уступки f2: -3x1 - x2 = f2_limit
x2_vals_f2 = 3 * x1_vals + f2_limit
plt.plot(x1_vals, x2_vals_f2, 'red', linewidth=2, label=fr'$x_2 = {f2_limit:.1f}+3x_1$ (уступка f2)')

plt.plot(opt3[0], opt3[1], 'go', markersize=10, label='Оптимум')

plt.xlabel(r'$x_1$')
plt.ylabel(r'$x_2$')
plt.title('После уступок f1 и f2 (третий график)')
plt.grid(True)
plt.legend()
plt.gca().set_aspect('equal', adjustable='box')
plt.xlim(0, 2 * n + 1)
plt.ylim(0, 1.5 * n + 1)
plt.show()

# Итоговое решение
print(f"\nИтоговое оптимальное решение:")
print(f"x1 = {opt3[0]:.3f}, x2 = {opt3[1]:.3f}")
