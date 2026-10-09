#Зубарев, вариант 5
import random
import matplotlib.pyplot as plt
import numpy as np

# Входные параметры
a1, b1 = 3, 16  # Параметры равномерного распределения S1
a2, b2 = 3, 3   # Параметры равномерного распределения S2
a3, b3, c = 4, 16, 8  # Параметры треугольного распределения S3
Q = 5  # Коэффициент Q
size = 200  # Размер выборки

def uniform_process(a, b, size):
    """Генерация равномерного случайного процесса."""
    return [(b - a) * random.random() + a for _ in range(size)]

def triangular_process(a, b, c, size):
    """Генерация треугольного случайного процесса."""
    result = []
    for _ in range(size):
        u = random.random()
        if u < (c - a) / (b - a):
            result.append(a + ((b - a) * (c - a) * u) ** 0.5)
        else:
            result.append(b - ((b - a) * (b - c) * (1 - u)) ** 0.5)
    return result

def simulate_process(size):
    """Моделирование случайного процесса S."""
    S1 = uniform_process(a1, b1, size)
    S2 = uniform_process(a2, b2, size)
    S3 = triangular_process(a3, b3, c, size)
    return [s1 + Q * s2 + s3 for s1, s2, s3 in zip(S1, S2, S3)]

# Генерация выборки случайного процесса
samples = simulate_process(size)

# Вычисление выборочных характеристик
mean_val = sum(samples) / size
std_val = (sum((x - mean_val) ** 2 for x in samples) / size) ** 0.5
print(f"Выборочное среднее: {mean_val:.4f}")
print(f"Выборочное стандартное отклонение: {std_val:.4f}")

# Гистограмма частотного распределения
hist_bins = 15
hist_range = min(samples), max(samples)
step = (hist_range[1] - hist_range[0]) / hist_bins
histogram = [0] * hist_bins
for s in samples:
    index = min(int((s - hist_range[0]) / step), hist_bins - 1)
    histogram[index] += 1

# Данные для графика функции вероятности треугольного распределения
x = np.linspace(a3, b3, 1000)
fx = np.where(x < c, 2 * (x - a3) / ((b3 - a3) * (c - a3)), 2 * (b3 - x) / ((b3 - a3) * (b3 - c)))

# Построение графиков
fig, axs = plt.subplots(3, 1, figsize=(8, 12))

# График функции вероятности
axs[0].plot(x, fx, label="PDF треугольного распределения", color='blue')
axs[0].set_xlabel("x")
axs[0].set_ylabel("Плотность вероятности")
axs[0].set_title("Функция вероятности треугольного распределения")
axs[0].legend()
axs[0].grid()

# График треугольного распределения
triangular_sample = triangular_process(a3, b3, c, size)
axs[1].hist(triangular_sample, bins=15, density=True, alpha=0.6, color='r', edgecolor='black')
axs[1].set_xlabel("Значения")
axs[1].set_ylabel("Частота")
axs[1].set_title("Гистограмма треугольного распределения")
axs[1].grid()

# Гистограмма выборки случайного процесса
bin_edges = [hist_range[0] + i * step for i in range(hist_bins + 1)]
axs[2].bar(bin_edges[:-1], histogram, width=step, edgecolor='black', alpha=0.7, color='g')
axs[2].set_xlabel("Значения случайного процесса")
axs[2].set_ylabel("Частота")
axs[2].set_title("Гистограмма выборки")
axs[2].grid()

plt.tight_layout()
plt.show()
