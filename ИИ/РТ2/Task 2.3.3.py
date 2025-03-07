import numpy as np
import pandas as pd
from math import sqrt
url='https://raw.githubusercontent.com/akmand/datasets/main/baby_names_2000.csv'
dataframe = pd.read_csv(url)
print(dataframe.head(5),"\n")
print(dataframe.tail(5),"\n")
print(dataframe.shape,"\n")
print(dataframe.describe(),"\n")
print(dataframe.iloc[1:4],"\n")
print(dataframe[dataframe['gender']=='F'],"\n")