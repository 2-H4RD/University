import numpy as np
import matplotlib.pyplot as plt

# Параметры сигнала
U_0 = 5e-3      # Амплитуда несущего сигнала (5 мВ)
m_1 = 0.6     # Коэффициент модуляции (60%)
f_0 = 125e6     # Частота несущего сигнала (125 МГц)
F_m1 = 400e3    # Частота модулирующего сигнала (400 кГц)
t_max = 0.5    # Продолжительность сигнала (секунды)
sampling_rate = 10000  # Частота дискретизации (Гц)

# Вектор времени
t = np.linspace(0, t_max, int(sampling_rate * t_max))

# Управляющий сигнал (модулирующий сигнал)
modulating_signal = m_1 * np.cos(2 * np.pi * F_m1 * t)

# Амплитудно-модулированный сигнал по заданной формуле
U_AM = U_0 * np.cos(2 * np.pi * f_0 * t) + (m_1 * U_0 / 2) * np.cos(2 * np.pi * (f_0 + F_m1) * t) + (m_1 * U_0 / 2) * np.cos(2 * np.pi * (f_0 - F_m1) * t)

# Управляющий сигнал (верхняя и нижняя огибающие)
envelope_upper = U_0 * (1 + modulating_signal)  # Верхняя огибающая
envelope_lower = U_0 * (1 - modulating_signal) - 2 * U_0  # Нижняя огибающая с сдвигом на -2U_0

# Расчеты амплитуд и частот
A_0 = U_0
A_n_bok = (m_1 * U_0) / 2
A_v_bok = (m_1 * U_0) / 2
f_n_bok = f_0 - F_m1
f_v_bok = f_0 + F_m1
delta_f_c = 2 * F_m1

# Вывод результатов
print("1. Амплитуда центральной гармоники:")
print(f"A0 = {A_0:.3e} В (формула: A0 = U0)")

print("\n2. Амплитуда нижней боковой гармоники:")
print(f"Aн.бок = {A_n_bok:.3e} В (формула: Aн.бок = (m1 * U0) / 2)")

print("\n3. Амплитуда верхней боковой гармоники:")
print(f"Ав.бок = {A_v_bok:.3e} В (формула: Ав.бок = (m1 * U0) / 2)")

print("\n4. Частота нижней боковой гармоники:")
print(f"fн.бок = {f_n_bok / 1e6:.3f} МГц (формула: fн.бок = f0 - Fm1)")

print("\n5. Частота верхней боковой гармоники:")
print(f"fв.бок = {f_v_bok / 1e6:.3f} МГц (формула: fв.бок = f0 + Fm1)")

print("\n6. Ширина спектра сигнала:")
print(f"дельта fc = {delta_f_c / 1e3:.3f} кГц (формула: дельта fc = 2 * Fm1)")

# Построение графиков
# График 1: Временная зависимость АМ сигнала и управляющих сигналов
plt.figure(figsize=(10, 4))
plt.plot(t, U_AM, label="АМ сигнал")
plt.plot(t, envelope_upper, label="Управляющий сигнал (верх)", color='r')  # Верхняя огибающая
plt.plot(t, envelope_lower, label="Управляющий сигнал (низ)", color='r')  # Нижняя огибающая
plt.title("Зависимость АМ сигнала от времени")
plt.xlabel("Время (с)")
plt.ylabel("Амплитуда")
plt.ylim(-1.5 * U_0, 1.5 * U_0)  # Подгонка масштаба амплитуды
plt.legend()
plt.grid(True)
plt.show()

# Построение графика АЧС
# Амплитуды для АЧС: несущая частота - U_0, побочные частоты - (m_1 * U_0) / 2
frequencies = [f_0 - F_m1, f_0, f_0 + F_m1]  # Частоты, на которых будут пики
amplitudes = [m_1 * U_0 / 2, U_0, m_1 * U_0 / 2]  # Амплитуды для этих частот

plt.figure(figsize=(10, 4))
for f, A in zip(frequencies, amplitudes):
    plt.vlines(f, 0, A, color='b', label=f'Частота {f} Гц' if f == f_0 else "")

# Подписи с формулами расчета амплитуд на графике АЧС
plt.text(f_0, U_0 + 0.2, f"$A_{{0}} = {U_0}$", horizontalalignment='center', verticalalignment='bottom', fontsize=10)
plt.text(f_0 - F_m1, (m_1 * U_0 / 2) + 0.2, f"$A_{{-}} = \\frac{{m_1 U_0}}{{2}} = {m_1 * U_0 / 2}$", horizontalalignment='center', verticalalignment='bottom', fontsize=10)
plt.text(f_0 + F_m1, (m_1 * U_0 / 2) + 0.2, f"$A_{{+}} = \\frac{{m_1 U_0}}{{2}} = {m_1 * U_0 / 2}$", horizontalalignment='center', verticalalignment='bottom', fontsize=10)

# Добавление делений на оси ординат с большим шагом
plt.yticks(np.arange(0, U_0 + 0.6, 0.2))

plt.title("АЧС амплитудно-модулированного сигнала")
plt.xlabel("Частота (Гц)")
plt.ylabel("Амплитуда")
plt.legend(loc='upper right')
plt.grid(True)
plt.show()
