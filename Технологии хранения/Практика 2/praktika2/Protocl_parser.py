import pandas as pd

# Путь к входному CSV файлу с данными Wireshark
input_csv_path = 'Capture.csv'

# Читаем данные из CSV файла
df = pd.read_csv(input_csv_path)

# Извлекаем все уникальные значения из колонки Protocol
unique_protocols = df['Protocol'].unique()

# Выводим все уникальные протоколы
print("Используемые протоколы в файле:")
for protocol in unique_protocols:
    print(protocol)
