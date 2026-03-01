"""
КДЗ: Многокритериальная оптимизация (f1,f2 -> min) генетическим алгоритмом.

Изменение по запросу: "чисто Парето метод"
- УБРАНА нормализованная взвешенная сумма (0.5*n1 + 0.5*n2).
- Селекция и “качество” решений определяются ТОЛЬКО Парето-подходом:
  1) Pareto-rank (номер фронта): 1 — недоминируемые, 2 — следующий слой, и т.д.
  2) Crowding distance (плотность/разреженность): чем больше, тем лучше (сохраняет разнообразие)

Турнирная селекция:
- выигрывает меньший rank
- при равном rank выигрывает больший crowding distance
- при полном равенстве — случайно

КДЗ пункт 5 (сортировка элитных точек):
- В “чистом Парето” нет одной скалярной функции, поэтому в качестве
  функции приспособленности для сортировки элит (архив элит = фронт rank=1)
  используем crowding distance (типично для Парето-алгоритмов).
- После завершения итераций:
  * считаем crowding distance для elite_archive
  * сортируем elite_archive по crowding (по убыванию)
  * печатаем TOP-30 и строим график: TOP-30 выделены на фоне всех элит

Графики:
1) Окно 1: начальная популяция (x1,x2)
2) Окно 2: все элитные точки (f1,f2) + выделение TOP-30 (по crowding)
3) Окно 3: 4 снимка фронта Парето (0,50,100,200) в одном окне (2x2)

Без def-функций, максимально линейно.
"""

import random
import matplotlib.pyplot as plt

# -----------------------------
# 0) Параметры
# -----------------------------
random.seed(42)

POP_SIZE = 80
GENERATIONS = 200  # хотим снимок на 200, значит реально надо дойти до gen=200 (нумерация с 0)

BITS_PER_VAR = 10
TOURNAMENT_SIZE = 3
P_CROSSOVER = 0.9
P_MUTATION = 0.01

X1_L, X1_H = 0.0, 79.0
X2_L, X2_H = 0.0, 79.0

TOTAL_BITS = 2 * BITS_PER_VAR
MAX_L = (2 ** BITS_PER_VAR) - 1

snapshot_gens = [0, 50, 100, 200]
if (GENERATIONS - 1) < snapshot_gens[-1]:
    GENERATIONS = snapshot_gens[-1] + 1  # чтобы цикл включал gen=200

pareto_snapshots = {}  # gen -> (list_f1, list_f2)
initial_x1 = []
initial_x2 = []

# -----------------------------
# 1) Инициализация популяции (генотип, код Грея)
# -----------------------------
population = []
for _ in range(POP_SIZE):
    genotype = [random.randint(0, 1) for _ in range(TOTAL_BITS)]
    population.append({
        "genotype": genotype,
        "x1": 0.0, "x2": 0.0,
        "obj1": 0.0, "obj2": 0.0,
        "rank": 0,          # Pareto-rank (1..)
        "crowding": 0.0,    # crowding distance
        "fitness": 0.0      # для КДЗ п.5: в этой версии = crowding
    })

elite_archive = []

# -----------------------------
# 2) Основной цикл ГА
# -----------------------------
for gen in range(GENERATIONS):

    # 2.1) Декодирование Gray->Binary->int->real, вычисление f1,f2
    for ind in population:
        g = ind["genotype"]

        # x1
        gray_x1 = g[:BITS_PER_VAR]
        binary_x1 = [0] * BITS_PER_VAR
        binary_x1[0] = gray_x1[0]
        for i in range(1, BITS_PER_VAR):
            binary_x1[i] = binary_x1[i - 1] ^ gray_x1[i]
        l1 = 0
        for bit in binary_x1:
            l1 = (l1 << 1) | bit
        x1 = X1_L + l1 * (X1_H - X1_L) / MAX_L

        # x2
        gray_x2 = g[BITS_PER_VAR:]
        binary_x2 = [0] * BITS_PER_VAR
        binary_x2[0] = gray_x2[0]
        for i in range(1, BITS_PER_VAR):
            binary_x2[i] = binary_x2[i - 1] ^ gray_x2[i]
        l2 = 0
        for bit in binary_x2:
            l2 = (l2 << 1) | bit
        x2 = X2_L + l2 * (X2_H - X2_L) / MAX_L

        ind["x1"] = x1
        ind["x2"] = x2
        ind["obj1"] = 0.2 * (x1 - 70.0) ** 2 + 0.8 * (x2 - 20.0) ** 2
        ind["obj2"] = 0.8 * (x1 - 10.0) ** 2 + 0.2 * (x2 - 70.0) ** 2

    if gen == 0:
        initial_x1 = [ind["x1"] for ind in population]
        initial_x2 = [ind["x2"] for ind in population]

    # ---------------------------------------------------------
    # 2.2) Быстрая недоминируемая сортировка (Pareto-rank)
    # ---------------------------------------------------------
    # dominates relation для минимизации:
    # a доминирует b, если (a1<=b1 and a2<=b2) and (a1<b1 or a2<b2)

    N = len(population)
    dominates_list = [[] for _ in range(N)]   # i -> список индексов, кого доминирует i
    domination_count = [0] * N                # сколько индивидов доминируют i
    fronts = []                               # список фронтов (каждый фронт = список индексов)

    for i in range(N):
        pi1 = population[i]["obj1"]
        pi2 = population[i]["obj2"]
        for j in range(N):
            if i == j:
                continue
            pj1 = population[j]["obj1"]
            pj2 = population[j]["obj2"]

            i_dom_j = (pi1 <= pj1 and pi2 <= pj2) and (pi1 < pj1 or pi2 < pj2)
            j_dom_i = (pj1 <= pi1 and pj2 <= pi2) and (pj1 < pi1 or pj2 < pi2)

            if i_dom_j:
                dominates_list[i].append(j)
            elif j_dom_i:
                domination_count[i] += 1

    first_front = []
    for i in range(N):
        if domination_count[i] == 0:
            population[i]["rank"] = 1
            first_front.append(i)

    fronts.append(first_front)

    current_rank = 1
    while True:
        next_front = []
        for i in fronts[current_rank - 1]:
            for j in dominates_list[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    population[j]["rank"] = current_rank + 1
                    next_front.append(j)
        if not next_front:
            break
        fronts.append(next_front)
        current_rank += 1

    # ---------------------------------------------------------
    # 2.3) Crowding distance для каждого фронта
    # ---------------------------------------------------------
    # crowding = 0 для всех
    for ind in population:
        ind["crowding"] = 0.0

    for front in fronts:
        if len(front) == 0:
            continue
        if len(front) == 1:
            population[front[0]]["crowding"] = float("inf")
            continue
        if len(front) == 2:
            population[front[0]]["crowding"] = float("inf")
            population[front[1]]["crowding"] = float("inf")
            continue

        # По obj1
        front_sorted_1 = sorted(front, key=lambda idx: population[idx]["obj1"])
        fmin = population[front_sorted_1[0]]["obj1"]
        fmax = population[front_sorted_1[-1]]["obj1"]
        population[front_sorted_1[0]]["crowding"] = float("inf")
        population[front_sorted_1[-1]]["crowding"] = float("inf")
        denom = (fmax - fmin) if (fmax - fmin) != 0 else None

        if denom is not None:
            for k in range(1, len(front_sorted_1) - 1):
                idx = front_sorted_1[k]
                if population[idx]["crowding"] != float("inf"):
                    prev_v = population[front_sorted_1[k - 1]]["obj1"]
                    next_v = population[front_sorted_1[k + 1]]["obj1"]
                    population[idx]["crowding"] += (next_v - prev_v) / denom

        # По obj2
        front_sorted_2 = sorted(front, key=lambda idx: population[idx]["obj2"])
        fmin = population[front_sorted_2[0]]["obj2"]
        fmax = population[front_sorted_2[-1]]["obj2"]
        population[front_sorted_2[0]]["crowding"] = float("inf")
        population[front_sorted_2[-1]]["crowding"] = float("inf")
        denom = (fmax - fmin) if (fmax - fmin) != 0 else None

        if denom is not None:
            for k in range(1, len(front_sorted_2) - 1):
                idx = front_sorted_2[k]
                if population[idx]["crowding"] != float("inf"):
                    prev_v = population[front_sorted_2[k - 1]]["obj2"]
                    next_v = population[front_sorted_2[k + 1]]["obj2"]
                    population[idx]["crowding"] += (next_v - prev_v) / denom

    # ---------------------------------------------------------
    # 2.4) Обновление архива элит (Парето-недоминируемые по всей истории)
    # ---------------------------------------------------------
    merged = elite_archive + population
    nondominated = []

    for i, p in enumerate(merged):
        dominated_by_someone = False
        for j, q in enumerate(merged):
            if i == j:
                continue
            not_worse_all = (q["obj1"] <= p["obj1"]) and (q["obj2"] <= p["obj2"])
            strictly_better_any = (q["obj1"] < p["obj1"]) or (q["obj2"] < p["obj2"])
            if not_worse_all and strictly_better_any:
                dominated_by_someone = True
                break
        if not dominated_by_someone:
            nondominated.append(p)

    # убираем дубли по (x1,x2)
    seen = set()
    elite_archive = []
    for p in nondominated:
        key = (round(p["x1"], 6), round(p["x2"], 6))
        if key not in seen:
            seen.add(key)
            elite_archive.append(p)

    # Снимки фронта Парето по поколениям (в пространстве критериев)
    if gen in snapshot_gens:
        pareto_snapshots[gen] = (
            [p["obj1"] for p in elite_archive],
            [p["obj2"] for p in elite_archive],
        )

    # ---------------------------------------------------------
    # 2.5) Репродукция: турнир -> кроссовер -> мутация
    # ---------------------------------------------------------
    if gen >= GENERATIONS - 1:
        break

    new_population = []
    while len(new_population) < POP_SIZE:

        # Турнир: выбираем лучшего по (rank, -crowding)
        contestants_idx = random.sample(range(N), TOURNAMENT_SIZE)
        winner_idx_1 = contestants_idx[0]
        for idx in contestants_idx[1:]:
            a = population[winner_idx_1]
            b = population[idx]
            if b["rank"] < a["rank"]:
                winner_idx_1 = idx
            elif b["rank"] == a["rank"]:
                # больше crowding лучше (больше разнообразие)
                if b["crowding"] > a["crowding"]:
                    winner_idx_1 = idx
                elif b["crowding"] == a["crowding"]:
                    if random.random() < 0.5:
                        winner_idx_1 = idx

        contestants_idx = random.sample(range(N), TOURNAMENT_SIZE)
        winner_idx_2 = contestants_idx[0]
        for idx in contestants_idx[1:]:
            a = population[winner_idx_2]
            b = population[idx]
            if b["rank"] < a["rank"]:
                winner_idx_2 = idx
            elif b["rank"] == a["rank"]:
                if b["crowding"] > a["crowding"]:
                    winner_idx_2 = idx
                elif b["crowding"] == a["crowding"]:
                    if random.random() < 0.5:
                        winner_idx_2 = idx

        g1 = population[winner_idx_1]["genotype"]
        g2 = population[winner_idx_2]["genotype"]

        # 3-точечный кроссовер (точка 2 фиксирована на границе блоков)
        if random.random() <= P_CROSSOVER:
            p1 = random.randint(1, BITS_PER_VAR - 1)
            p2 = BITS_PER_VAR
            p3 = random.randint(BITS_PER_VAR + 1, TOTAL_BITS - 1)

            child1_genotype = g1[0:p1] + g2[p1:p2] + g1[p2:p3] + g2[p3:TOTAL_BITS]
            child2_genotype = g2[0:p1] + g1[p1:p2] + g2[p2:p3] + g1[p3:TOTAL_BITS]
        else:
            child1_genotype = g1[:]
            child2_genotype = g2[:]

        # мутация (побитовая)
        for i in range(TOTAL_BITS):
            if random.random() < P_MUTATION:
                child1_genotype[i] ^= 1
        for i in range(TOTAL_BITS):
            if random.random() < P_MUTATION:
                child2_genotype[i] ^= 1

        new_population.append({
            "genotype": child1_genotype,
            "x1": 0.0, "x2": 0.0,
            "obj1": 0.0, "obj2": 0.0,
            "rank": 0, "crowding": 0.0, "fitness": 0.0
        })
        if len(new_population) < POP_SIZE:
            new_population.append({
                "genotype": child2_genotype,
                "x1": 0.0, "x2": 0.0,
                "obj1": 0.0, "obj2": 0.0,
                "rank": 0, "crowding": 0.0, "fitness": 0.0
            })

    population = new_population

# -----------------------------
# 3) КДЗ пункт 5: "сортировка элит по приспособленности"
# В чистом Парето-стиле в качестве приспособленности элит используем crowding distance.
# -----------------------------
# Для elite_archive (он уже недоминируемый) считаем crowding distance как для одного фронта.

M = len(elite_archive)
if M > 0:
    for p in elite_archive:
        p["crowding"] = 0.0

if M == 1:
    elite_archive[0]["crowding"] = float("inf")
elif M == 2:
    elite_archive[0]["crowding"] = float("inf")
    elite_archive[1]["crowding"] = float("inf")
elif M >= 3:
    # по obj1
    idxs = list(range(M))
    idxs_sorted_1 = sorted(idxs, key=lambda i: elite_archive[i]["obj1"])
    fmin = elite_archive[idxs_sorted_1[0]]["obj1"]
    fmax = elite_archive[idxs_sorted_1[-1]]["obj1"]
    elite_archive[idxs_sorted_1[0]]["crowding"] = float("inf")
    elite_archive[idxs_sorted_1[-1]]["crowding"] = float("inf")
    denom = (fmax - fmin) if (fmax - fmin) != 0 else None
    if denom is not None:
        for k in range(1, M - 1):
            i = idxs_sorted_1[k]
            if elite_archive[i]["crowding"] != float("inf"):
                prev_v = elite_archive[idxs_sorted_1[k - 1]]["obj1"]
                next_v = elite_archive[idxs_sorted_1[k + 1]]["obj1"]
                elite_archive[i]["crowding"] += (next_v - prev_v) / denom

    # по obj2
    idxs_sorted_2 = sorted(idxs, key=lambda i: elite_archive[i]["obj2"])
    fmin = elite_archive[idxs_sorted_2[0]]["obj2"]
    fmax = elite_archive[idxs_sorted_2[-1]]["obj2"]
    elite_archive[idxs_sorted_2[0]]["crowding"] = float("inf")
    elite_archive[idxs_sorted_2[-1]]["crowding"] = float("inf")
    denom = (fmax - fmin) if (fmax - fmin) != 0 else None
    if denom is not None:
        for k in range(1, M - 1):
            i = idxs_sorted_2[k]
            if elite_archive[i]["crowding"] != float("inf"):
                prev_v = elite_archive[idxs_sorted_2[k - 1]]["obj2"]
                next_v = elite_archive[idxs_sorted_2[k + 1]]["obj2"]
                elite_archive[i]["crowding"] += (next_v - prev_v) / denom

# fitness = crowding (чтобы формально было поле "приспособленности")
for p in elite_archive:
    p["fitness"] = p["crowding"]

# сортировка элит: больше crowding => выше приоритет (лучше разнообразие фронта)
elite_archive.sort(key=lambda p: p["fitness"], reverse=True)

TOP_K = 30
top_k = elite_archive[:TOP_K]

print("\nTOP-30 элитных точек, отсортированных по crowding distance")
print("   # |    x1      x2   |      f1         f2    |  crowding")
print("-" * 66)
for i, p in enumerate(top_k, start=1):
    cd = p["crowding"]
    cd_str = "inf" if cd == float("inf") else f"{cd:9.6f}"
    print(f"{i:4d} | {p['x1']:7.3f} {p['x2']:7.3f} | {p['obj1']:10.3f} {p['obj2']:10.3f} | {cd_str}")
print(f"... всего в архиве: {len(elite_archive)} точек")

# -----------------------------
# 4) Окно 1: начальная популяция (x1, x2)
# -----------------------------
plt.figure()
plt.scatter(initial_x1, initial_x2)
plt.title("Начальная популяция (поколение 0) в пространстве решений")
plt.xlabel("x1")
plt.ylabel("x2")
plt.grid(True)
plt.xlim(X1_L, X1_H)
plt.ylim(X2_L, X2_H)

# -----------------------------
# 5) Окно 2: выделение TOP-30 на фоне всех элитных точек (f1, f2)
# -----------------------------
all_elite_f1 = [p["obj1"] for p in elite_archive]
all_elite_f2 = [p["obj2"] for p in elite_archive]
top_f1 = [p["obj1"] for p in top_k]
top_f2 = [p["obj2"] for p in top_k]

plt.figure()
plt.scatter(all_elite_f1, all_elite_f2, alpha=0.35, label="all elite (Pareto archive)")
plt.scatter(top_f1, top_f2, label="TOP-30 по crowding")
plt.title("TOP-30 элитных по crowding на фоне всех элит")
plt.xlabel("f1 (min)")
plt.ylabel("f2 (min)")
plt.grid(True)
plt.legend()

# -----------------------------
# 6) Окно 3: 4 subplots (0,50,100,200) — снимки фронта Парето (f1,f2)
# -----------------------------
all_f1 = []
all_f2 = []
for g in snapshot_gens:
    s = pareto_snapshots.get(g)
    if s is not None:
        s1, s2 = s
        all_f1.extend(s1)
        all_f2.extend(s2)

x_min = min(all_f1) if all_f1 else 0.0
x_max = max(all_f1) if all_f1 else 1.0
y_min = min(all_f2) if all_f2 else 0.0
y_max = max(all_f2) if all_f2 else 1.0

pad_x = 0.05 * (x_max - x_min) if x_max > x_min else 1.0
pad_y = 0.05 * (y_max - y_min) if y_max > y_min else 1.0

fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.flatten()

for idx, g in enumerate(snapshot_gens):
    ax = axes[idx]
    s = pareto_snapshots.get(g)

    if s is None:
        ax.set_title(f"Поколение {g} (нет данных)")
        ax.set_xlabel("f1 (min)")
        ax.set_ylabel("f2 (min)")
        ax.grid(True)
        continue

    s1, s2 = s
    ax.scatter(s1, s2)
    ax.set_title(f"Фронт Парето — поколение {g} (n={len(s1)})")
    ax.set_xlabel("f1 (min)")
    ax.set_ylabel("f2 (min)")
    ax.grid(True)
    ax.set_xlim(x_min - pad_x, x_max + pad_x)
    ax.set_ylim(y_min - pad_y, y_max + pad_y)

plt.tight_layout()
plt.show()