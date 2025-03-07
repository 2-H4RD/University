import numpy as np
import matplotlib.pyplot as plt
from numpy import *
from numpy.random import *

# генерируем случайные x и y
delta = 1.0
x = linspace(-5,5,11)
y = x**2 + delta * (rand(11) - 0.5)
x+= delta * (rand(11) - 0.5)

# Нахождение коэффициентов функции вида y = ax^2 + bx + c методом наименьших квадратов
# задаем вектор m = [X**2, x, E]
m = vstack((x**2,x,ones(11))).T

# находим коэффициенты при составляющих вектора m
s = np.linalg.lstsq(m,y,rcond = None)[0]

# на отрезке [-5, 5]
x_prec = linspace(-5, 5, 101)

# рисуем точки
plt.plot(x,y,'D')

# рисуем кривую вида y = ax^2 + bx + c, подставляя из решения коэффициенты s[0], s[1], s[2]
plt.plot(x_prec, s[0] * x_prec**2 + s[1] * x_prec+s[2], '-', lw = 2)
plt.grid()
plt.show()