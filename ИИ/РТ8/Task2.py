import pandas as pd
import matplotlib.pyplot as plt
import scipy.cluster.hierarchy as shc
from sklearn.cluster import AgglomerativeClustering

url = 'https://gist.githubusercontent.com/netj/8836201/raw/6f9306ad21398ea43cba4f7d537619d0e07d5ae3/iris.csv'
customer_data = pd.read_csv(url)
customer_data.head()
print(customer_data.shape)
data = customer_data.iloc[:, 2:4].values
plt.figure(figsize=(10,7))
dend = shc.dendrogram(shc.linkage(data, method='ward'))
plt.show()

cluster = AgglomerativeClustering(n_clusters=3, affinity='euclidean', linkage='ward')
print(cluster.fit_predict(data))
plt.figure(figsize=(10,7))
plt.scatter(data[:,0], data[:,1], c=cluster.labels_, cmap='rainbow')
plt.show();
