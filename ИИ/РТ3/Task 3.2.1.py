import pandas as pd

# Создать признаки
dataframe = pd.DataFrame({'оценка': ['низкая', 'низкая', 'средняя', 'средняя', 'высокая']})
# Создать словарь преобразования шкалы
scale_mapper = {'низкая':1,'средняя':2,'высокая':3}

# Заменить значения признаков значениями словаря
dataframe = dataframe['оценка'].replace(scale_mapper)
print(dataframe)