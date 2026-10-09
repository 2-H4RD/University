import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
iris=sns.load_dataset('iris')

plt.figure(figsize=(16, 7))

# Левый график
plt.subplot(121)
sns.scatterplot(
data=iris, # из этой таблицы нарисовать точки
    x='petal_width', y='petal_length',
    # с этими координатами,
    hue='species', # для которых цвет определить согласно этому столбцу
    s=70 # размер точек
)
plt.xlabel('Длина лепестка, см')
plt.ylabel('Ширина лепестка, см')
plt.legend() # добавить легенду
plt.grid() # добавить сетку

# Правый график аналогично
plt.subplot(122)
sns.scatterplot(data=iris, x='sepal_width', y='sepal_length', hue='species', s=70)
plt.xlabel('Длина чашелистика, см')
plt.ylabel('Ширина чашелистика, см')
plt.legend()
plt.grid()
plt.show()