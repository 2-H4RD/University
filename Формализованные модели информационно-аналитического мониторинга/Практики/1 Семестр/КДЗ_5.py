import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import linprog, minimize_scalar
from shapely.geometry import Polygon
from scipy.linalg import solve
from itertools import combinations

# Вариант 5
n = 5

# Матрица ограничений (левая часть Ax ≤ b)
A = np.array([
    [-1, -2],  # -x1 - 2x2 ≤ -2n  (x1 + 2x2 ≥ 2n)
    [1, -2],   # x1 - 2x2 ≤ n
    [-3, 2],   # -3x1 + 2x2 ≤ 2n
    [-1, 0],   # -x1 ≤ 0  (x1 ≥ 0)
    [1, 0],    # x1 ≤ 4n
    [0, -1],   # -x2 ≤ 0  (x2 ≥ 0)
    [0, 1]     # x2 ≤ 3n
])
b = np.array([
    -2*n,
     n,
    2*n,
     0,
    4*n,
     0,
    3*n
])

# Критерии
def f1(x): return x[0] + x[1]
def f2(x): return -3*x[0] + x[1]
def f3(x): return x[0] - 3*x[1]

# Линейная максимизация одного критерия
def maximize_criterion(c):
    res = linprog(-np.array(c), A_ub=A, b_ub=b, method='highs')
    return res.x, -res.fun

# Находим оптимумы по каждому критерию
opt1, f1_max = maximize_criterion([1,1])
opt2, f2_max = maximize_criterion([-3,1])
opt3, f3_max = maximize_criterion([1,-3])
print(f"Оптимальная точка для f1: {opt1} с макс. {f1_max:.2f}")
print(f"Оптимальная точка для f2: {opt2} с макс. {f2_max:.2f}")
print(f"Оптимальная точка для f3: {opt3} с макс. {f3_max:.2f}")

# Строим вершины ОДЗ
vertices = []
for i,j in combinations(range(len(A)),2):
    M = np.array([A[i], A[j]])
    rhs = np.array([b[i], b[j]])
    if np.linalg.matrix_rank(M)==2:
        try:
            pnt = solve(M,rhs)
            if all(np.dot(A,pnt) <= b + 1e-6):
                vertices.append(tuple(pnt))
        except:
            pass
vertices = list(set(vertices))
center = np.mean(vertices,axis=0)
vertices.sort(key=lambda p: np.arctan2(p[1]-center[1], p[0]-center[0]))

# Метрика ρ и её градиент (динамически по f*_max)
def rho(x):
    return (f1(x) - f1_max)**2 + (f2(x) - f2_max)**2 + (f3(x) - f3_max)**2

def grad_rho(x):
    # градиенты критериев f1,f2,f3
    g1 = np.array([1, 1])
    g2 = np.array([-3, 1])
    g3 = np.array([1, -3])
    # производная суммы квадратов
    return 2*(f1(x)-f1_max)*g1 + 2*(f2(x)-f2_max)*g2 + 2*(f3(x)-f3_max)*g3

# Проверка ОДЗ
def in_D(x):
    return all(np.dot(A,x) <= b)

# Франк–Вульфа: линейная подзадача по ρ + line-search по ρ
def frank_wolfe_algorithm(x0, max_iter=200, tol=10**-3, eps=1e-4):
    x_old = x0.copy()
    history = [x_old]
    for k in range(1, max_iter+1):
        # градиент метрики
        g = grad_rho(x_old)
        # линейная подзадача: min g^T x
        res = linprog(g, A_ub=A, b_ub=b, bounds=[(0,4*n),(0,3*n)], method='highs')
        x_bar = res.x
        # одномерный поиск λ ∈ [0,1]
        d = x_bar - x_old
        phi = lambda lam: rho(x_old + lam*d)
        lam = minimize_scalar(phi, bounds=(0,1), method='bounded').x
        x_new = x_old + lam*d

        # проверки
        if not in_D(x_new):
            print(f"Завершено на итерации {k} (выход за ОДЗ)")
            break
        if np.linalg.norm(x_new-x_old) < tol:
            print(f"Завершено на итерации {k} (шаг < tol={tol})")
            break
        if abs(rho(x_new)-rho(x_old)) < eps:
            print(f"Завершено на итерации {k} (Δρ < eps={eps})")
            break

        print(f"Итерация {k}: x_bar={x_bar}, λ={lam:.4f}, x_new={x_new}")
        history.append(x_new)
        x_old = x_new
    else:
        print(f"Достигнуто max_iter={max_iter}")
    return x_old, np.array(history)

# Запуск алгоритма и визуализация
x0 = np.array([n, 2*n])
opt_x, hist = frank_wolfe_algorithm(x0)
print("Оптимальная точка (FW):", opt_x)

# График 1: ОДЗ
plt.figure(figsize=(6,6))
poly = Polygon(vertices); xv,yv = poly.exterior.xy
plt.plot(xv,yv,'k-',linewidth=2)
plt.xlim(-1,4*n+1); plt.ylim(-1,3*n+1)
plt.gca().set_aspect('equal'); plt.title("ОДЗ"); plt.grid(True)
plt.show()

# График 2: ОДЗ + опт. точки
plt.figure(figsize=(6,6))
plt.plot(xv,yv,'k-')
for name,pt in zip(['f1','f2','f3'],[opt1,opt2,opt3]):
    plt.scatter(*pt,color='green')
    plt.text(pt[0]+0.5,pt[1]+0.5,f"{name}[{pt[0]:.1f},{pt[1]:.1f}]")
plt.xlim(-1,4*n+1); plt.ylim(-1,3*n+1)
plt.gca().set_aspect('equal'); plt.title("ОДЗ и оптимальные точки"); plt.grid(True)
plt.show()

# График 3: ОДЗ + путь FW
plt.figure(figsize=(6,6))
plt.plot(xv,yv,'k-')
xs, ys = hist[:,0], hist[:,1]
plt.plot(xs, ys,'o-',color='red')  # Все точки, кроме финальной

# Отображаем все точки, полученные на каждой итерации
for i, (xx, yy) in enumerate(hist):
    if i == len(hist) - 1:  # Финальная точка
        plt.scatter(xx, yy, color='green', s=100, label=f'X{i} (Final)', edgecolors='black')  # Увеличиваем размер для финальной точки
    else:
        plt.scatter(xx, yy, color='red')  # Все остальные точки

    # Подписываем каждую точку
    plt.text(xx + 0.5, yy + 0.5, f"X{i}")

plt.xlim(-1, 4 * n + 1); plt.ylim(-1, 3 * n + 1)
plt.gca().set_aspect('equal')
plt.title("Итерации Франк-Вульфа")
plt.grid(True)
plt.legend()
plt.show()
