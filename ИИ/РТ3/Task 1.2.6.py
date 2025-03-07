import numpy as np
x = np.array([0, 0, 0])
y = np.array([3, 3, 3])
w = np.array([0, 0, 1])
print(np.linalg.norm(x - y))
print(np.linalg.norm(x - y) ** 2)
print(np.linalg.norm(x - y, ord=np.inf))
print(np.linalg.norm(x - y, ord=1))