import numpy as np
import pandas as pd
from math import sqrt
def length (a,b):
    sum = 0
    for i in range(len(a)):
        sum +=(a[i]- b[i])**2
    return sqrt(sum)
a=pd.Series([1,2,3,4,5])
b=pd.Series([10,20,30,40,50])
print(length(a,b))

