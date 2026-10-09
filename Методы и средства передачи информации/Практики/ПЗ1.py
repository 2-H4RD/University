import numpy as np
import matplotlib.pyplot as plt

# Исходные данные (вариант 5)
U0 = 5 * 10**-3  # Амплитуда несущего сигнала, В
f0 = 125 * 10**6  # Частота несущего, Гц
m1 = 0.6  # Глубина амплитудной модуляции
Fm1 = 400 * 10**3  # Частота модулирующего сигнала, Гц
Fm2 = 2 * Fm1  # Вторая частота модулирующего сигнала

# === ЗАДАНИЕ 1.2 ===
# Формулы
modulating_signal_12 = "u_m(t) = m1 * cos(2 * π * Fm1 * t) + m1 * cos(2 * π * Fm2 * t)"
am_signal_12 = "u_am(t) = U0 * (1 + u_m(t)) * cos(2 * π * f0 * t)"

# Вычисления
A0 = U0
An1_bok = (m1 / 2) * U0
fv_bok = f0 + max(Fm1,Fm2)
fn_bok = f0 - max(Fm1,Fm2)
Df_c = 2 * max(Fm1,Fm2)

# Вывод результатов задания 1.2
print("=== Результаты задания 1.2 ===")
print("Формула модулирующего сигнала:", modulating_signal_12)
print("Формула амплитудно-модулированного сигнала:", am_signal_12)
print(f"Амплитуда центральной гармоники (A0): {A0:.6f} В")
print(f"Амплитуда боковых гармоник (An1_bok): {An1_bok:.6f} В")
print(f"Частоты боковых гармоник: {fn_bok} Гц, {fv_bok} Гц")
print(f"Ширина спектра сигнала (Df_c): {Df_c} Гц")

# Временные характеристики
T = 1 / max(Fm1,Fm2)
fs = 10 * f0

# Формирование сигналов для 1.2
modulating_signal = m1 * (np.cos(2 * np.pi * Fm1 * np.linspace(0, 5 * T, 1000)) + np.cos(2 * np.pi * Fm2 * np.linspace(0, 5 * T, 1000)))
am_signal = U0 * (1 + modulating_signal) * np.cos(2 * np.pi * f0 * np.linspace(0, 5 * T, 1000))

# === ЗАДАНИЕ 1.3 ===
m2 = 0.5 * m1  # Из условия задания 1.3
modulating_signal_13 = "u_m(t) = m1 * cos(2 * π * Fm1 * t) + m2 * cos(2 * π * Fm2 * t)"
am_signal_13 = "u_am(t) = U0 * (1 + u_m(t)) * cos(2 * π * f0 * t)"

# Вычисления для 1.3
An2_bok = (m2 / 2) * U0
Df_c_13 = 2 * max(Fm1,Fm2)

# Вывод результатов задания 1.3
print("\n=== Результаты задания 1.3 ===")
print("Формула модулирующего сигнала:", modulating_signal_12)
print("Формула амплитудно-модулированного сигнала:", am_signal_12)
print(f"Амплитуда центральной гармоники (A0): {A0:.6f} В")
print(f"Амплитуда боковых гармоник (An2_bok): {An2_bok:.6f} В")
print(f"Частоты боковых гармоник: {fn_bok} Гц, {fv_bok} Гц")
print(f"Ширина спектра сигнала (Df_c): {Df_c} Гц")

# Формирование сигналов для 1.3
modulating_signal_13 = m1 * np.cos(2 * np.pi * Fm1 * np.linspace(0, 5 * T, 1000)) + m2 * np.cos(2 * np.pi * Fm2 * np.linspace(0, 5 * T, 1000))
am_signal_13 = U0 * (1 + modulating_signal_13) * np.cos(2 * np.pi * f0 * np.linspace(0, 5 * T, 1000))

# Построение графиков задания 1.2 и 1.3 в одном окне
fig, axs = plt.subplots(2, 2, figsize=(12, 10))

# График из задания 1.2
axs[0, 0].plot(np.linspace(0, 5 * T, 1000) * 10**6, am_signal, label='AM Signal')
axs[0, 0].set_title("Временная диаграмма АМ-сигнала (Задание 1.2)")
axs[0, 0].set_xlabel("Время, мкс")
axs[0, 0].set_ylabel("Амплитуда, В")
axs[0, 0].grid()
axs[0, 0].legend()

axs[0, 1].stem([fn_bok / 10**6, f0 / 10**6, fv_bok / 10**6], [An1_bok, A0, An1_bok], basefmt=" ")
axs[0, 1].set_title("Амплитудный спектр АМ-сигнала (Задание 1.2)")
axs[0, 1].set_xlabel("Частота, МГц")
axs[0, 1].set_ylabel("Амплитуда,В")
axs[0, 1].grid()

# График из задания 1.3
axs[1, 0].plot(np.linspace(0, 5 * T, 1000) * 10**6, am_signal_13, label='AM Signal')
axs[1, 0].set_title("Временная диаграмма АМ-сигнала (Задание 1.3)")
axs[1, 0].set_xlabel("Время, мкс")
axs[1, 0].set_ylabel("Амплитуда, В")
axs[1, 0].grid()
axs[1, 0].legend()

axs[1, 1].stem([fn_bok /10**6, f0 / 10**6, fv_bok / 10**6], [An2_bok, A0, An2_bok], basefmt=" ")
axs[1, 1].set_title("Амплитудный спектр АМ-сигнала (Задание 1.3)")
axs[1, 1].set_xlabel("Частота, МГц")
axs[1, 1].set_ylabel("Амплитуда,В")
axs[1, 1].grid()

# Подгоняем макет
plt.tight_layout()
plt.show()

#Вывод
#Спектр сигнала напрямую зависит от Fm и никак не зависит от m
