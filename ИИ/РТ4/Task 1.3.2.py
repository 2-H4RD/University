import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from  sklearn import metrics

#5
x = np.array([5.0, 5.2, 5.4,5.6, 5.8, 6.0])
y = np.array([2.0, 4.0, 4.0, 3.0, 3.0, 3.0])
print('X = ',x)
print('Y = ',y)

A1 = np.vstack([x,np.ones(len(x))]).T
k, b = np.linalg.lstsq(A1, y, rcond = None)[0]
plt.plot(x, y, 'D', label = 'исходные данные', markersize= 10)
plt.plot(x, k*x + b, 'r',label = 'Линейная экстраполяция ')
plt.legend()
plt.show()

A2 = np.vstack([x**2,x,np.ones(len(x))]).T
a,b,c=np.linalg.lstsq(A2, y, rcond = None)[0]
x_prec = np.linspace(5, 6, 6)
plt.plot(x, y, 'D')
plt.plot(x_prec, a * x_prec ** 2 + b * x_prec + c, '-', lw = 2)
plt.show()