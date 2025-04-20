import numpy as np
import matplotlib.pyplot as plt

# Порог и границы для генерации точек
n = 5
f1_min, f1_max, f2_min, f2_max = 0, 3*n, 0, 3*n

# 1) Генерация допустимых точек
def generate_feasible_points(N=100):
    pts = []
    while len(pts) < N:
        x = np.random.uniform(f1_min, f1_max)
        y = np.random.uniform(f2_min, f2_max)
        if x * y >= n:
            pts.append([x, y])
    return np.array(pts)

# 2) Вершины и рёбра по Грею
def generate_vertices(mu_min, mu_max):
    return [
        np.array([mu_min[0], mu_min[1]]),  # код 00
        np.array([mu_max[0], mu_min[1]]),  # код 01
        np.array([mu_max[0], mu_max[1]]),  # код 11
        np.array([mu_min[0], mu_max[1]]),  # код 10
    ]

def build_edges():
    return [(0,1),(1,2),(2,3),(3,0)]

# 3) Пересечение ребра с линией μ1+μ2=1
def intersect_edge(p, q):
    Lp, Lq = p.sum() - 1, q.sum() - 1
    if Lp * Lq > 0:
        return None
    # вертикальное ребро?
    if np.isclose(p[0], q[0]):
        x = p[0]; y = 1 - x
    else:
        y = p[1]; x = 1 - y
    return np.array([x, y])

# 4) Построение матрицы B для заданного интервала весов
def construct_polyhedral_cone(mu_min, mu_max):
    # случай точных весов
    if np.allclose(mu_min, mu_max):
        return np.array([mu_min], dtype=float)
    verts = generate_vertices(mu_min, mu_max)
    B = []
    for i,j in build_edges():
        P = intersect_edge(verts[i], verts[j])
        if P is None: continue
        if mu_min[0] <= P[0] <= mu_max[0] and mu_min[1] <= P[1] <= mu_max[1]:
            B.append(P)
    return np.unique(np.array(B), axis=0) if B else np.empty((0,2))

# 5) Проверка: Fi доминируется Fj по конусу B?
def is_dominated_by(Fi, Fj, B):
    if B.size == 0:
        return False
    diff = Fi - Fj  # для минимизации
    ge = [np.dot(b, diff) >= 0 for b in B]
    gt = [np.dot(b, diff) >  0 for b in B]
    return all(ge) and any(gt)

# 6) Однократное построение парето через B0 = B([0,0],[1,1])
def build_pareto(fx):
    B0 = construct_polyhedral_cone([0,0], [1,1])
    pareto = []
    for Fi in fx:
        if not any(is_dominated_by(Fi, Fj, B0) for Fj in fx if not np.allclose(Fi, Fj)):
            pareto.append(Fi)
    return np.array(pareto)

# 7) Ω‑оптимальные через B для текущих весов
def build_omega(pareto, B):
    omega = []
    for Fi in pareto:
        if not any(is_dominated_by(Fi, Fj, B) for Fj in pareto if not np.allclose(Fi, Fj)):
            omega.append(Fi)
    return np.array(omega)

# 8) Рисуем три графика
def plot_all(fx, pareto, omega, B, mu_min, mu_max, case_num):
    fig, axs = plt.subplots(1,3,figsize=(18,6))

    # 1) конус
    ax = axs[0]
    ax.set_title(f'Кейс {case_num}: конус')
    for v in B:
        ax.plot([0,v[0]],[0,v[1]],'r-')
    ax.plot([0,1],[1,0],'b-')
    ax.plot([mu_min[0],mu_max[0]],[mu_min[1],mu_min[1]],'b-')
    ax.plot([mu_min[0],mu_max[0]],[mu_max[1],mu_max[1]],'b-')
    ax.plot([mu_min[0],mu_min[0]],[mu_min[1],mu_max[1]],'b-')
    ax.plot([mu_max[0],mu_max[0]],[mu_min[1],mu_max[1]],'b-')
    ax.set_xlabel('f1'); ax.set_ylabel('f2'); ax.grid(True)

    # 2) парето
    ax = axs[1]
    ax.set_title(f'Кейс {case_num}: парето')
    ax.scatter(fx[:,0], fx[:,1], s=10, alpha=0.3, color='black')
    if pareto.size:
        ax.scatter(pareto[:,0], pareto[:,1], s=20, color='green')
    ax.set_xlabel('f1'); ax.set_ylabel('f2'); ax.grid(True)

    # 3) омега
    ax = axs[2]
    ax.set_title(f'Кейс {case_num}: омега')
    ax.scatter(fx[:,0], fx[:,1], s=10, alpha=0.3, color='black')
    non_omega = np.array([p for p in pareto if not any(np.allclose(p,w) for w in omega)])
    if non_omega.size:
        ax.scatter(non_omega[:,0], non_omega[:,1], s=20, color='green')
    if omega.size:
        ax.scatter(omega[:,0], omega[:,1], s=20, color='red')
    ax.set_xlabel('f1'); ax.set_ylabel('f2'); ax.grid(True)

    plt.tight_layout()
    plt.show()

# 9) Основной анализ
def analyze_all():
    cases = [
        (0.2,0.6,0.4,0.8),
        (0.4,0.8,0.2,0.6),
        (0.3,0.6,0.3,0.6),
        (0.3, 0.3, 0.7, 0.7)
    ]
    for N in [1000]:
        fx = generate_feasible_points(N)
        pareto = build_pareto(fx)                                # только один раз
        print(f"N={N}, |F|={len(fx)}, |Pareto|={len(pareto)}")
        for idx,(a1,b1,a2,b2) in enumerate(cases,1):
            mu_min, mu_max = [a1,a2],[b1,b2]
            B = construct_polyhedral_cone(mu_min, mu_max)
            omega = build_omega(pareto, B)
            print(f"  Case {idx}: |Ω|={len(omega)}")
            plot_all(fx, pareto, omega, B, mu_min, mu_max, idx)

if __name__=="__main__":
    analyze_all()
