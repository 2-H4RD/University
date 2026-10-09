import numpy as np
a=np.indices((8,8)).sum(axis=0)%2
print(a)