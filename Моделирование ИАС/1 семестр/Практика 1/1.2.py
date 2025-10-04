# Вариант 5, Зубарев
import random
import math
import matplotlib.pyplot as plt

def box_muller(size, mx, dx):
    """Генерация нормальных случайных чисел методом Бокса-Мюллера."""
    numbers = []
    for _ in range(size):
        u1, u2 = random.random(), random.random()
        z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
        numbers.append(mx + dx * z)
    return numbers

def clt(size, mx, dx):
    """Генерация нормальных случайных чисел методом ЦПТ."""
    numbers = []
    for _ in range(size):
        sum_uniform = sum(random.random() for _ in range(12)) - 6  # Центрируем сумму
        numbers.append(mx + dx * sum_uniform / math.sqrt(12 / 12))
    return numbers

def compute_stats(data):
    """Вычисление среднего и дисперсии."""
    mean_sample = sum(data) / len(data)
    var_sample = sum((x - mean_sample) ** 2 for x in data) / len(data)
    return mean_sample, var_sample

def quality_score(mean_sample, mean_true, var_sample, var_true):
    """Оценка качества (0 - плохо, 1 - идеально)."""
    mean_err = abs(mean_sample - mean_true) / abs(mean_true)
    var_err = abs(var_sample - var_true) / abs(var_true)
    return max(0, 1 - (mean_err + var_err) / 2)

size = 1000
mx, dx = 22, 0.416

sample_bm = box_muller(size, mx, dx)
sample_clt = clt(size, mx, dx)

mean_bm, var_bm = compute_stats(sample_bm)
mean_clt, var_clt = compute_stats(sample_clt)

var_theoretical = dx ** 2
quality_bm = quality_score(mean_bm, mx, var_bm, var_theoretical)
quality_clt = quality_score(mean_clt, mx, var_clt, var_theoretical)

print(f"Мат. ожидание: теор. {mx}, Бокс-Мюллер {mean_bm:.4f}, ЦПТ {mean_clt:.4f}")
print(f"Дисперсия: теор. {var_theoretical:.4f}, Бокс-Мюллер {var_bm:.4f}, ЦПТ {var_clt:.4f}")
print(f"Качество: БМ {quality_bm:.4f}, ЦПТ {quality_clt:.4f}")

plt.hist(sample_bm, bins=30, alpha=0.5, label=f"Бокс-Мюллер (кач-во {quality_bm:.4f})", density=True, color='blue')
plt.hist(sample_clt, bins=30, alpha=0.5, label=f"ЦПТ (кач-во {quality_clt:.4f})", density=True, color='red')
plt.axvline(mx, color='black', linestyle='dashed', linewidth=2, label=f"Мат. ожидание: {mx}")

plt.title("Гистограмма нормального распределения")
plt.xlabel("Значение")
plt.ylabel("Плотность")
plt.legend()
plt.show()
