import time
import random
import matplotlib.pyplot as plt
from pynput import keyboard

# Генерация фразы для анализа клавиатурного почерка
def generate_analysis_phrase():
    return "Сегодня мы изучаем особенности клавиатурного почерка"

# Основной класс для анализа клавиатурного почерка
class KeyboardAnalyzer:
    def __init__(self, analysis_phrase):
        self.analysis_phrase = analysis_phrase
        self.input_phrase = ""
        self.start_time = None
        self.key_times = []
        self.release_times = []

    def on_press(self, key):
        try:
            if self.start_time is None:
                self.start_time = time.time()

            char = key.char if hasattr(key, 'char') else str(key)
            self.input_phrase += char

            # Записываем время нажатия
            self.key_times.append((char, time.time() - self.start_time))
        except Exception as e:
            print(f"Ошибка: {e}")

    def on_release(self, key):
        try:
            char = key.char if hasattr(key, 'char') else str(key)
            self.release_times.append((char, time.time() - self.start_time))
        except Exception as e:
            print(f"Ошибка: {e}")

        if key == keyboard.Key.enter:  # Завершение ввода при нажатии Enter
            return False

    def calculate_metrics(self):
        dwell_times = []
        flight_times = []
        for i, (char, press_time) in enumerate(self.key_times):
            # Рассчитываем Dwell Time
            if i < len(self.release_times) and self.release_times[i][0] == char:
                dwell_time = self.release_times[i][1] - press_time
                dwell_times.append(dwell_time)

            # Рассчитываем Flight Time
            if i > 0:
                flight_time = press_time - self.key_times[i - 1][1]
                flight_times.append(flight_time)

        avg_speed = len(self.key_times) / (self.key_times[-1][1] if self.key_times else 1)
        rhythm = sum(abs(flight_times[i] - flight_times[i - 1]) for i in range(1, len(flight_times))) / len(flight_times) if len(flight_times) > 1 else 0

        return {
            "dwell_times": dwell_times,
            "flight_times": flight_times,
            "average_speed": avg_speed,
            "rhythm": rhythm,
            "keys": [item[0] for item in self.key_times]
        }

    def plot_analysis(self, metrics):
        keys = metrics["keys"]
        times = [item[1] for item in self.key_times]

        # График времени нажатий клавиш
        plt.figure(figsize=(6, 4))
        plt.plot(times, [i for i in range(len(times))], marker='o', label="Нажатия клавиш")
        for i, key in enumerate(keys):
            plt.text(times[i], i, key, fontsize=9, ha='right')
        plt.xlabel("Время (секунды)")
        plt.ylabel("Порядок нажатия")
        plt.title("Нажатия клавиш")
        plt.legend()
        plt.grid()
        plt.show()

        # График Dwell Time
        plt.figure(figsize=(6, 4))
        plt.bar(range(len(metrics["dwell_times"])), metrics["dwell_times"], label="Dwell Time")
        plt.xticks(range(len(keys)), keys, rotation=45)
        plt.xlabel("Символы")
        plt.ylabel("Время (сек)")
        plt.title("Dwell Time (Удержание клавиши)")
        plt.grid()
        plt.show()

        # График Flight Time
        plt.figure(figsize=(6, 4))
        plt.bar(range(len(metrics["flight_times"])), metrics["flight_times"], label="Flight Time")
        plt.xticks(range(len(keys) - 1), keys[:-1], rotation=45)
        plt.xlabel("Символы")
        plt.ylabel("Время (сек)")
        plt.title("Flight Time (Время между нажатиями)")
        plt.grid()
        plt.show()

        # Ритмичность и средняя скорость
        plt.figure(figsize=(6, 4))
        plt.bar([0, 1], [metrics["average_speed"], metrics["rhythm"]], tick_label=["Скорость", "Ритм"])
        plt.title("Средняя скорость и ритмичность")
        plt.grid()
        plt.show()

# Основная функция
if __name__ == "__main__":
    print("Анализатор клавиатурного почерка")
    analysis_phrase = generate_analysis_phrase()
    print(f"Введите любую фразу. Например: {analysis_phrase}")

    analyzer = KeyboardAnalyzer(analysis_phrase)

    with keyboard.Listener(
            on_press=analyzer.on_press,
            on_release=analyzer.on_release) as listener:
        listener.join()

    metrics = analyzer.calculate_metrics()
    analyzer.plot_analysis(metrics)
