from tabulate import tabulate

A_matrix = [
    [21, 12, 15, 23, 18],
    [11, 33, 28, 16, 19]
]

m, n = len(A_matrix), len(A_matrix[0])
B = [0] * n  # B_x
A = [0] * m  # A_y
count_A = [0] * m
count_B = [0] * n
history = []
total_iter = 10000
for k in range(1, total_iter + 1):
    if k == 1:
        i = 1
    else:
        i = A.index(min(A)) + 1
    count_A[i - 1] += 1
    for x in range(n):
        B[x] += A_matrix[i - 1][x]
    j = B.index(max(B)) + 1
    count_B[j - 1] += 1
    for y in range(m):
        A[y] += A_matrix[y][j - 1]
    alpha_bar = max(B) / k
    beta_bar = min(A) / k
    nu_bar = (alpha_bar + beta_bar) / 2
    history.append([
        k, i,
        B[0], B[1], B[2], B[3], B[4],
        round(alpha_bar, 6),
        j,
        A[0], A[1],
        round(beta_bar, 6),
        round(nu_bar, 6)
    ])

headers = ["k", "i", "B_1", "B_2", "B_3", "B_4", "B_5", "ᾱ(k)", "j", "A_1", "A_2", "β̄(k)", "ῡ(k)"]
print("Первые 10 итераций:")
print(tabulate(history[:10], headers=headers, tablefmt="grid"))
print("\nПоследние 5 итераций:")
print(tabulate(history[-5:], headers=headers, tablefmt="grid"))
p = [count / total_iter for count in count_A]
q = [count / total_iter for count in count_B]
print(f"\nОценка цены игры на итерации {total_iter}: {history[-1][-1]:.6f}")
print("\nОптимальные смешанные стратегии (эмпирические):")
print(f"Игрок A (протоколы):   p = [{p[0]:.6f}, {p[1]:.6f}]")
print(f"Игрок B (атаки):       q = [{q[0]:.6f}, {q[1]:.6f}, {q[2]:.6f}, {q[3]:.6f}, {q[4]:.6f}]")