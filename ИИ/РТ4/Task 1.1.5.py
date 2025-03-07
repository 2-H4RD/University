import numpy as np
import scipy as sp
import matplotlib.pyplot as plt

#1
# Добавим шума в данные, сделанные по функции f(x,b) с коэффициентами b = (0.25, 0.75)
beta = (2, 10)
def f1(x, b0, b1):
    return b0 + b1 * x
# зададим массив из точек xi
xdata = np.linspace(0, 5, 50)
# создаем теоретически правильные значения точек yi (без шума)
y = f1(xdata, *beta)
# зашумляем эти данные
ydata = y + 0.05 * np.random.rand(len(xdata))
beta_opt, beta_cov = sp.optimize.curve_fit(f1, xdata, ydata)
# Вычислим линейное отклонение
lin_dev = sum(beta_cov[0])
print('Линейное отклонение 1 = ', lin_dev)

# Вычислим квадратичное уравнение
residuals = ydata - f1(xdata, *beta_opt)
fres = sum(residuals**2)

fig, ax = plt.subplots()
ax.scatter(xdata,ydata)
ax.plot(xdata, y, 'r', lw=2)
ax.plot(xdata, f1(xdata, *beta_opt), 'b', lw=2)
ax.set_xlim(0, 5)
ax.set_xlabel(r"$x$", fontsize = 18)
ax.set_ylabel(r"$f(x,\beta)$", fontsize = 18)
plt.show()

#2
beta = (10, 3, 10)
def f2(x, b0, b1, b2):
    return b0 + b1 * x + b2 * x * x
# зададим массив из точек xi
xdata = np.linspace(0, 5, 50)
# создаем теоретически правильные значения точек yi (без шума)
y = f2(xdata, *beta)
# зашумляем эти данные
ydata = y + 0.05 * np.random.rand(len(xdata))
beta_opt, beta_cov = sp.optimize.curve_fit(f2, xdata, ydata)

# Вычислим линейное отклонение
lin_dev = sum(beta_cov[0])
print('Линейное отклонение 2 = ', lin_dev)

# Вычислим квадратичное уравнение
residuals = ydata - f2(xdata, *beta_opt)
fres = sum(residuals**2)


fig, ax = plt.subplots()
ax.scatter(xdata,ydata)
ax.plot(xdata, y, 'r', lw=2)
ax.plot(xdata, f2(xdata, *beta_opt), 'b', lw=2)
ax.set_xlim(0, 5)
ax.set_xlabel(r"$x$", fontsize = 18)
ax.set_ylabel(r"$f(x,\beta)$", fontsize = 18)
plt.show()

#3
# Добавим шума в данные, сделанные по функции f(x,b) с коэффициентами b = (1, 2)
beta = (5, 5)
def f(x, b0, b1):
    return b0 + b1 * np.log(x)
# зададим массив из точек xi
xdata = np.linspace(1, 5, 50)
# создаем теоретически правильные значения точек yi (без шума)
y = f(xdata, *beta)
# зашумляем эти данные
ydata = y + 0.05 * np.random.rand(len(xdata))
beta_opt, beta_cov = sp.optimize.curve_fit(f, xdata, ydata)

# Вычислим линейное отклонение
lin_dev = sum(beta_cov[0])
print('Линейное отклонение 3 = ', lin_dev)

# Вычислим квадратичное уравнение
residuals = ydata -f(xdata, *beta_opt)
fres = sum(residuals**2)


fig,ax = plt.subplots()
ax.scatter(xdata,ydata)
ax.plot(xdata,y,'r',lw =2 )
ax.plot(xdata,f(xdata,*beta_opt),'b',lw = 2)
ax.set_xlim(0,5)
ax.set_xlabel(r"$x$", fontsize = 18)
ax.set_ylabel(r"$f(x,\beta)$", fontsize = 18)
plt.show()

#4
# Добавим шума в данные, сделанные по функции f(x,b) с коэффициентами b = (1, 2)
beta = (10, 1)
def f(x, b0, b1):
    return b0 * x ** b1
# зададим массив из точек xi
xdata = np.linspace(1, 5, 50)
# создаем теоретически правильные значения точек yi (без шума)
y = f(xdata, *beta)
# зашумляем эти данные
ydata = y + 0.05 * np.random.rand(len(xdata))
beta_opt, beta_cov = sp.optimize.curve_fit(f, xdata, ydata)

# Вычислим линейное отклонение
lin_dev = sum(beta_cov[0])
print('Линейное отклонение 4 = ', lin_dev)

# Вычислим квадратичное уравнение
residuals = ydata - f(xdata, *beta_opt)
fres = sum(residuals**2)


fig, ax = plt.subplots()
ax.scatter(xdata,ydata)
ax.plot(xdata, y, 'r', lw=2)
ax.plot(xdata, f(xdata, *beta_opt), 'b', lw=2)
ax.set_xlim(0, 5)
ax.set_xlabel(r"$x$", fontsize = 18)
ax.set_ylabel(r"$f(x,\beta)$", fontsize = 18)
plt.show()