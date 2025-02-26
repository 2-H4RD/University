# Вариант 5, Зубарев
import numpy as np
import matplotlib.pyplot as plt


def uniform_inverse_transform(size, a=0, b=1):
    """Генерация равномерно распределенных чисел методом обратных функций."""
    r = [np.random.random() for _ in range(size)]  # Генерация случайных чисел в [0,1]
    return [a + (b - a) * ri for ri in r]  # Преобразование в диапазон [a,b]


def compute_statistics(sample):
    """Вычисление выборочных статистических характеристик."""
    n = len(sample)
    mean_sample = sum(sample) / n  # Вычисление выборочного среднего
    variance_sample = sum((x - mean_sample) ** 2 for x in sample) / n  # Вычисление дисперсии
    return mean_sample, variance_sample


def evaluate_quality(mean_sample, mean_theoretical, variance_sample, variance_theoretical):
    """Оценка качества распределения (0 - плохо, 1 - идеально)."""
    mean_diff = abs(mean_sample - mean_theoretical) / abs(mean_theoretical)
    variance_diff = abs(variance_sample - variance_theoretical) / abs(variance_theoretical)
    quality = max(0, 1 - (mean_diff + variance_diff) / 2)
    return quality


size = 100  # Размер выборки
a, b = 25, 40  # Границы отрезка для равномерного распределения

sample_ab = uniform_inverse_transform(size, a, b)  # [a,b]

# Теоретические характеристики
mean_theoretical = (a + b) / 2 #Вычисление теоритического мат.ожидания
variance_theoretical = ((b - a) ** 2) / 12 # Вычисление теоритической квадратичной дисперсии

# Выборочные характеристики
mean_sample, variance_sample = compute_statistics(sample_ab)
quality = evaluate_quality(mean_sample, mean_theoretical, variance_sample, variance_theoretical)

# Вывод результатов
print(f"Границы распределения: a = {a}, b = {b}")
print(f"Теоретическое мат. ожидание: {mean_theoretical:.4f}, Выборочное: {mean_sample:.4f}")
print(f"Теоретическая дисперсия: {variance_theoretical:.4f}, Выборочная: {variance_sample:.4f}")
print(f"Качество распределения: {quality:.4f}")

# Гистограмма распределения
plt.hist(sample_ab, bins=30, density=True, alpha=0.6, color='b', label="Выборка")
plt.axvline(mean_sample, color='r', linestyle='dashed', linewidth=2,
            label=f"Выборочное мат. ожидание: {mean_sample:.4f}")
plt.axvline(mean_theoretical, color='g', linestyle='dashed', linewidth=2,
            label=f"Теоретическое мат. ожидание: {mean_theoretical:.4f}")

# Подпись теоретической и выборочной дисперсии
plt.text(b - 0.5, 0.8,
            f"Теор. дисперсия: {variance_theoretical:.4f}\nВыбор. дисперсия: {variance_sample:.4f}\nКачество: {quality:.4f}",
            fontsize=10, bbox=dict(facecolor='white', alpha=0.5))

plt.title(f"Гистограмма равномерного распределения [{a},{b}]")
plt.xlabel("Значение")
plt.ylabel("Плотность")
plt.legend()
plt.show()

