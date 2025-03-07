import numpy as np
import pandas as pd
from math import sqrt
from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler
df_test = pd.DataFrame({'A': [14.00, 90.20, 90.95, 96.27, 91.21],
                        'B': [103.02, 107.26, 110.35, 114.23, 114.68],
                        'C': ['big', 'small', 'big', 'small', 'small']})
scaler = MinMaxScaler(feature_range=(0, 1))
df_test[['A', 'B']] = scaler.fit_transform(df_test[['A', 'B']])
print(df_test)