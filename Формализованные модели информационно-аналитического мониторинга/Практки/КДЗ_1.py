# Зубарев, вариант 5
import numpy as np
import matplotlib.pyplot as plt

n = 5
f1_min, f1_max = n / 2, 3 * n
f2_min, f2_max = n / 2, 2 * n
num_points = 5
points = []

while len(points) < num_points:
    f1 = np.random.uniform(f1_min, f1_max)
    f2 = np.random.uniform(f2_min, f2_max)
    if ((f1 - n) / (4 * n**2)) + ((f2 - n)**2 / n**2) <= 1:
        points.append((f1, f2))

points = np.array(points)

plt.figure(figsize=(8, 6))
plt.scatter(points[:, 0], points[:, 1], color='blue', s=10)

for i, (x, y) in enumerate(points):
    plt.text(x, y, str(i + 1), fontsize=6, verticalalignment='bottom', horizontalalignment='right')

plt.xlabel('f1')
plt.ylabel('f2')
plt.title('Случайные точки в ограниченной области')
plt.grid(True)
plt.show()

