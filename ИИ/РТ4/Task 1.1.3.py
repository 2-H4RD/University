import numpy as np
import matplotlib.pyplot as plt
from numpy import *
from numpy.random import *

def print_graph3(delta):
    x = linspace(-5, 5, 11)
    y = x ** 3 + delta * (rand(11) - 0.5)
    x += delta * (rand(11) - 0.5)
    m = vstack((x ** 3, x ** 2, x, ones(11))).T
    s = np.linalg.lstsq(m, y, rcond=None)[0]
    x_prec = linspace(-5, 5, 101)
    plt.plot(x, y, 'D')
    plt.plot(x_prec, s[0] * x_prec ** 3 + s[1] * x_prec ** 2 + s[2] * x_prec + s[3], '-', lw=2)
    plt.grid()
    plt.title('Третий порядок')
    plt.show()

def print_graph2(delta):
    x = linspace(-5, 5, 11)
    y = x ** 2 + delta * (rand(11) - 0.5)
    x += delta * (rand(11) - 0.5)
    m = vstack((x ** 2, x, ones(11))).T
    s = np.linalg.lstsq(m, y, rcond=None)[0]
    x_prec = linspace(-5, 5, 101)
    plt.plot(x, y, 'D')
    plt.plot(x_prec, s[0] * x_prec ** 2 + s[1] * x_prec + s[2], '-', lw=2)
    plt.grid()
    plt.title('Второй порядок')
    plt.show()

def print_graph1(delta):
    x = linspace(-5, 5, 11)
    y = x + delta * (rand(11) - 0.5)
    x += delta * (rand(11) - 0.5)
    m = vstack((x, ones(11))).T
    s = np.linalg.lstsq(m, y, rcond=None)[0]
    x_prec = linspace(-5, 5, 101)
    plt.plot(x, y, 'D')
    plt.plot(x_prec, s[0] * x_prec + s[1], '-', lw=2)
    plt.grid()
    plt.title('Первый  порядок')
    plt.show()

delta = 1.0
print_graph3(delta)
print_graph2(delta)
print_graph1(delta)