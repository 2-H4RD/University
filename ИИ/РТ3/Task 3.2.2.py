import pandas as pd
from sklearn.feature_extraction import DictVectorizer

data_dict = [{"красный": 2, "синий": 4},
            {"красный": 4, "синий": 3},
            {"красный": 1, "желтый": 2},
            {"красный": 2, "желтый": 2}]
# Создать векторизатор словаря
dictvectorizer = DictVectorizer(sparse=False)
# Конвертировать словарь в матрицу признаков
features = dictvectorizer.fit_transform(data_dict)
print(features)