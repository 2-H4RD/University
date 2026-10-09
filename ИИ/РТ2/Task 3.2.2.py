import numpy as np
import pandas as pd
from math import sqrt
from sklearn import preprocessing
x = np.array([[-1000.1], [-200.2], [500.5], [600.6], [9000.9]])
scaler = preprocessing.StandardScaler()
standardized = scaler.fit_transform(x)
print('Среднее:', round(standardized.mean()))
print('Стандартное отклонение:', standardized.std())
print(standardized)