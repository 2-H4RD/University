import numpy as np
import pandas as pd
lst = [1, 2, 3, 4, 5]
d = {'a': 1, 'b': 2, 'c': 3}
ndarr = np.array([1, 2, 3, 4, 5])
s1 = pd.Series(lst)
s2 = pd.Series(d)
s3 = pd.Series(ndarr, ['a', 'b', 'c', 'd', 'e'])
print(s1)
print(s2)
print(s3)