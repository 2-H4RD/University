import pandas as pd
from sklearn.feature_extraction import DictVectorizer

data_dict = [{'карие': 0, 'голубые': 0, 'зеленые': 1},
            {'карие': 1, 'голубые': 1, 'зеленые':0},
            {'карие': 1, 'голубые': 1, 'зеленые':1},
            {'карие': 0, 'голубые': 0, 'зеленые':0}]
# Создать векторизатор словаря
dictvectorizer = DictVectorizer(sparse=False)
# Конвертировать словарь в матрицу признаков
features = dictvectorizer.fit_transform(data_dict)
print(features)