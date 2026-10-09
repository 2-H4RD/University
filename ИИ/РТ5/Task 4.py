import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn import metrics


#1
url = 'https://raw.githubusercontent.com/likarajo/petrol_consumption/master/data/petrol_consumption.csv'
dataframe = pd.read_csv(url)
dataframe.head()
dataframe.describe()

# Нарисуем точечную диаграмму
dataframe.plot(x="Petrol_tax",y=['Paved_Highways','Petrol_Consumption','Population_Driver_licence(%)'],kind="bar")
plt.xlabel("Штаты")
plt.ylabel("Потребление бензина")
plt.show()

X = dataframe[['Average_income','Population_Driver_licence(%)','Petrol_Consumption']]
y = dataframe['Petrol_tax']
print(X)
print(y)

# Теперь, когда у нас есть атрибуты и метки, необходимо разделить их на а обучающий и тестовый наборы.
# Приведенный фрагмент разделяет 80% данных на обучающий набор, а 20% данных - на набор тестов
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 0)

# далее можно обучить алгоритм линейной регрессии
# необходимо импортировать класс LinearRegression, создать его экземпляр и вызвать метод fit()
regressor = DecisionTreeRegressor()
regressor.fit(X_train, y_train)

from sklearn import tree
tree.plot_tree(regressor)

#Построим прогноз:
y_pred = regressor.predict(X_test)

#Теперь сравним некоторые из наших прогнозируемых значений с фактическими значениями:
df=pd.DataFrame({'Actual':y_test, 'Predicted':y_pred})
#Расчитаем среднюю абсолютную и среднеквадратичную ошибку регрессии:
print('Mean Squared Error:', metrics.mean_squared_error(y_test, y_pred))
print('Mean Absolute Error:', metrics.mean_absolute_error(y_test, y_pred))

print(metrics.mean_absolute_error(y_test, y_pred) / np.average(y) * 100)