import numpy as np
def sqr_euclidean_distance(v1, v2):
    return sum((x - y) ** 2 for x, y in zip(v1, v2))
def weighted_euclidean_distance(v1, v2, v3):
    return sum((x - y) ** 2 * z for x, y, z in zip(v1, v2, v3)) ** 0.5
def manhattan_distance(v1, v2):
    return sum(abs(x - y) for (x, y) in zip(v1, v2))
def chebyshev_distance(v1, v2):
    return max(abs(x - y) for (x, y) in zip(v1, v2))
x = np.array([0, 0, 0])
y = np.array([3, 3, 3])
z = np.array([0, 0, 1])
print(sqr_euclidean_distance(x, y))
print(weighted_euclidean_distance(x, y, z))
print(manhattan_distance(x, y))
print(chebyshev_distance(x, y))