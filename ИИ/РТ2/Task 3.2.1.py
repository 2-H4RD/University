import numpy as np
import pandas as pd
from math import sqrt
from sklearn import preprocessing
feature = np.array([[-500.5], [-100.1], [0], [100.1], [900.9]])
minmax_scale = preprocessing.MinMaxScaler(feature_range=(0, 1))
scaled_feature = minmax_scale.fit_transform(feature)
print(scaled_feature)