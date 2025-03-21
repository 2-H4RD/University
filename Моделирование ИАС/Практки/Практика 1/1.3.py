#Вариант 5, Зубарев
import random
import math
import matplotlib.pyplot as plt

a, b = 5, 32
m = (a + b) / 2

size = 1000
data = []

while len(data) < size:
    y = random.uniform(a, b)
    u = random.uniform(0, 1)
    f_y = (6 / (4 * (b - a))) * (1 - 4 * ((y - m) / (b - a)) ** 2)
    if u <= f_y:
        data.append(y)

mean_sample = sum(data) / len(data)
squared_mean_sample = sum(x ** 2 for x in data) / len(data)
var_sample = squared_mean_sample - mean_sample ** 2

theoretical_mean = m
theoretical_squared_mean = (20 * theoretical_mean ** 2 + (b - a) ** 2) / 20
theoretical_var = theoretical_squared_mean - theoretical_mean ** 2

quality = max(0, 1 - (abs(mean_sample - theoretical_mean) / abs(theoretical_mean) + abs(var_sample - theoretical_var) / abs(theoretical_var)) / 2)

print(f"Мат. ожидание: теор. {theoretical_mean}, выборочное {mean_sample:.4f}")
print(f"Дисперсия: теор. {theoretical_var:.4f}, выборочная {var_sample:.4f}")
print(f"Качество распределения: {quality:.4f}")

plt.hist(data, bins=30, density=True, alpha=0.6, color='g', label=f"Качество {quality:.4f}")
plt.axvline(theoretical_mean, color='black', linestyle='dashed', linewidth=2, label=f"Мат. ожидание: {theoretical_mean}")
plt.title("Гистограмма случайных чисел методом Неймана")
plt.xlabel("Значение")
plt.ylabel("Плотность")
plt.legend()
plt.show()
