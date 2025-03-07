import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

dataset = sns.load_dataset('iris')
print(dataset, '\n')

print(dataset.shape,'\n')

print(dataset.head())