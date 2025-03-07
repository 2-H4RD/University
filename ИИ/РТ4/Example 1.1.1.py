import numpy as np
import matplotlib.pyplot as plt
x = np.array([0, 1, 2, 3])
y = np.array([-1, 0.2, 0.9, 2.1])

# Перепишем линейное уравнение y = kx + b как y = Ap, где А = [[ x 1 ]] и p = [[m], [c]]
# Построим A по Х:

A = np.vstack([x,np.ones(len(x))]).T
print(A) # print забыли

# Используем метод lstsq для решения его относительно вектора p
m, c = np.linalg.lstsq(A, y, rcond = None)[0]
print(m, c)

# Построим график полученной прямой и укажем на нем точки
plt.plot(x, y, 'o', label = 'исходные данные', markersize= 10)

plt.plot(x, m*x + c, 'r',label = 'Линейная экстраполяция ')
plt.legend()
plt.show()