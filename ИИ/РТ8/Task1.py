import matplotlib.pyplot as plt
import seaborn as sns; sns.set()
from sklearn.cluster import KMeans
import numpy as np
from sklearn.datasets import load_iris
X = np.array([[5,3], [10,15], [15,12], [24,10], [30,45], [85,70], [71,80], [60,78], [55,52], [80,91],])
plt.scatter(X[:, 0], X[:, 1], s = 20)
print(plt.show())
kmeans = KMeans(n_clusters = 3)
kmeans.fit(X)
y_kmeans = kmeans.predict(X)
plt.scatter(X[:, 0], X[:, 1], c = y_kmeans, s = 20, cmap='summer')
centers = kmeans.cluster_centers_
plt.scatter(centers[:, 0], centers[:, 1], c = 'blue', s = 100, alpha=0.9)
plt.show()
dataframe = load_iris()

X = dataframe.data
kmeans = KMeans(n_clusters = 3)
kmeans.fit(dataframe.data)
y_kmeans = kmeans.predict(dataframe.data)
plt.scatter(X[:, 0], X[:, 1], c = y_kmeans, s = 20, cmap='summer')
centers = kmeans.cluster_centers_
plt.scatter(centers[:, 0], centers[:, 1], c = 'blue', s = 100, alpha=0.9)
plt.show()