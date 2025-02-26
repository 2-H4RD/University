#Вариант 5, Зубарев
import random
import math
import matplotlib.pyplot as plt

p = 0.595  # Параметр геометрического распределения
q = 1 - p
size = 1000
data = []

# Генерация случайных чисел методом "розыгрыша жребия"
for _ in range(size):
    u = random.random()  # Генерация равномерного случайного числа
    k = 1  # Начальное значение k
    cumulative_prob = p  # Начальная суммарная вероятность
    while u > cumulative_prob:
        k += 1
        cumulative_prob += (q ** (k - 1)) * p  # Вычисление границ отрезка для метода жребия
    data.append(k)

# Вычисление выборочного математического ожидания
mean_sample = sum(data) / len(data)

# Вычисление выборочного среднего квадрата
squared_mean_sample = sum(x ** 2 for x in data) / len(data)

# Вычисление выборочной дисперсии
var_sample = squared_mean_sample - mean_sample ** 2

# Теоретическое математическое ожидание
theoretical_mean = 1 / p

# Теоретическая дисперсия
theoretical_var = q / (p ** 2)

# Оценка качества распределения
quality = max(0, 1 - (abs(mean_sample - theoretical_mean) / abs(theoretical_mean) + abs(var_sample - theoretical_var) / abs(theoretical_var)) / 2)

# Вывод результатов
print(f"Мат. ожидание: теор. {theoretical_mean:.4f}, выборочное {mean_sample:.4f}")
print(f"Дисперсия: теор. {theoretical_var:.4f}, выборочная {var_sample:.4f}")
print(f"Качество распределения: {quality:.4f}")

# Построение гистограммы
plt.hist(data, bins=30, density=True, alpha=0.6, color='b', label=f"Качество {quality:.4f}")
plt.axvline(theoretical_mean, color='black', linestyle='dashed', linewidth=2, label=f"Мат. ожидание: {theoretical_mean:.4f}")
plt.title("Гистограмма случайных чисел по геометрическому распределению")
plt.xlabel("Значение")
plt.ylabel("Плотность")
plt.legend()
plt.show()
