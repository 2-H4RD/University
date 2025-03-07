import pandas as pd
url='https://raw.githubusercontent.com/akmand/datasets/main/baby_names_2000.csv'
dataframe = pd.read_csv(url)
print(dataframe)