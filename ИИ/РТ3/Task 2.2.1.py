import numpy as np
from sklearn.neighbors import KNeighborsClassifier
X=np.array([[-1,-1],[-2,1],[-3,2],[1,1],[2,1],[3,2]])
target=[0,0,0,1,1,1]
K = 3
model = KNeighborsClassifier(n_neighbors=K)
model.fit(X,target)
print(model)
print('(-2,-2) in class ', model.predict([[-2,-2]]),'\n')
print('(1,3) in class ', model.predict([[1,3]]),'\n')

