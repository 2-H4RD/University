import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn import metrics

url = r"https://raw.githubusercontent.com/likarajo/petrol_consumption/master/data/petrol_consumption.csv"

dataframe_raw = pd.read_csv(url, on_bad_lines='skip')

petrol_tax = dataframe_raw.iloc[:, 0].values  # pt
avg_income = dataframe_raw.iloc[:, 1].values  # ai
paved_highways = dataframe_raw.iloc[:, 2].values  # ph
pop_driver_license = dataframe_raw.iloc[:, 3].values  # pdl
petrol_consumption = dataframe_raw.iloc[:, 4].values  # pc

df_pt = pd.DataFrame(np.array(petrol_tax).transpose())
df_ai = pd.DataFrame(np.array(avg_income).transpose())
df_ph = pd.DataFrame(np.array(paved_highways).transpose())
df_pdl = pd.DataFrame(np.array(pop_driver_license).transpose())
df_pc = pd.DataFrame(np.array(petrol_consumption).transpose())

df_pt = df_pt.rename(columns={0: 'Petrol tax'}, inplace=False)
df_ai = df_ai.rename(columns={0: 'Average income'}, inplace=False)
df_ph = df_ph.rename(columns={0: 'Paved Highways'}, inplace=False)
df_pdl = df_pdl.rename(columns={0: 'Population Driver licence'}, inplace=False)
df_pc = df_pc.rename(columns={0: 'Petrol Consumption'}, inplace=False)

frames = [df_pt, df_ai, df_ph, df_pdl, df_pc]
dataset = pd.concat(frames, axis=1, join="inner")
print(dataset)
x = dataset[['Petrol tax', 'Average income', 'Paved Highways', 'Population Driver licence']]
y = dataset['Petrol Consumption']
x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.5, random_state=0)

regressor = LinearRegression()
regressor.fit(x_train, y_train)

coefficient_df = pd.DataFrame(regressor.coef_, x.columns, columns=['Coefficient'])
y_pred = regressor.predict(x_test)
df = pd.DataFrame({'Actual': y_test, 'Predict': y_pred})

print('Mean Squared Error: ', metrics.mean_squared_error(y_test, y_pred))

print(coefficient_df)
print(df)
df = pd.DataFrame({'Actual': y_test, 'Predicted': y_pred})
df.plot(kind='bar')
print(df)