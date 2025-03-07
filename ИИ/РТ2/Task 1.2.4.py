import numpy as np
a = np.arange(25).reshape(5, 5)
print(a,'\n')
a[[0, 1]] = a[[1, 0]]
print(a)
