import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import StandardScaler
url='https://raw.githubusercontent.com/akmand/datasets/master/iris.csv'
dataframe=pd.read_csv(url)
scaler = MinMaxScaler()
dataframe[['sepal_length_cm']] = scaler.fit_transform(dataframe[['sepal_length_cm']])
scaler = StandardScaler()
dataframe[['sepal_width_cm']] = scaler.fit_transform(dataframe[['sepal_width_cm']])
print(dataframe)
