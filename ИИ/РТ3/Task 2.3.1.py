import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
iris = sns.load_dataset('iris')

def init_model(k, X_train, y_train, X_test): # Установите другое количество ближайших соседей (k = 1, 5, 10).
    model = KNeighborsClassifier(n_neighbors=k)
    model.fit(X_train, y_train)
    print(model)
    y_pred = model.predict(X_test)
    return y_pred

def graph(y_test, X_test, y_pred): #  Постройте графики
    plt.figure(figsize=(10, 7))
    sns.scatterplot(x='petal_width', y='petal_length', data=iris, hue='species', s=70)
    plt.xlabel("Длина лепестка, см")
    plt.ylabel("Ширина лепестка, см")
    plt.legend(loc=2)
    plt.grid()

    for i in range(len(y_test)):
        if np.array(y_test)[i] != y_pred[i]:
            plt.scatter(X_test.iloc[i, 3], X_test.iloc[i, 2], color='red', s=150)
    plt.show()

X_train, X_test, y_train, y_test = train_test_split(
    iris.iloc[:, :-1],
    iris.iloc[:, -1],
    test_size = 0.15 # Установите размер тестовой выборки 15% от всего датасета.
)

X_train.shape, X_test.shape, y_train.shape, y_test.shape

X_train.head()
y_train.head()

k = [3,5,10,20,50]
accurascy=[]
for i in k:
    y_pred = init_model(i, X_train, y_train, X_test)
    accurascy.append(accuracy_score(y_pred,y_test))
    graph(y_test, X_test, y_pred)
for i in range(5):
    print('K = ', k[i], ' Accuarcy = ', accurascy[i])