import pandas as pd

# IP-адрес хоста, который всегда должен быть Source
host_ip = "192.168.179.201"

# Чтение исходного CSV файла
input_csv_path = 'Detailed_capture.csv'  # Укажите путь к вашему файлу
df = pd.read_csv(input_csv_path)

# Создаем словарь для хранения информации о сессиях
sessions = {}

# Проходим по каждой строке исходного файла
for index, row in df.iterrows():
    src = row['Source']
    dst = row['Destination']
    length = int(row['Length'])
    # Определяем, кто из них является хостом (192.168.179.201)
    if src == host_ip:
        # Хост отправляет данные, сервер принимает
        session_key = (src, dst)
        source_packets = 1
        source_length = length
        destination_packets = 0
        destination_length = 0
    elif dst == host_ip:
        # Сервер отправляет данные, хост принимает
        session_key = (dst, src)
        source_packets = 0
        source_length = 0
        destination_packets = 1
        destination_length = length
    else:
        # Если ни один из IP не является хостом, пропускаем строку
        continue

    # Обновляем информацию о сессии
    if session_key not in sessions:
        sessions[session_key] = {
            'Source_Packets': source_packets,
            'Source_Length': source_length,
            'Destination_Packets': destination_packets,
            'Destination_Length': destination_length,
        }
    else:
        sessions[session_key]['Source_Packets'] += source_packets
        sessions[session_key]['Source_Length'] += source_length
        sessions[session_key]['Destination_Packets'] += destination_packets
        sessions[session_key]['Destination_Length'] += destination_length

# Формируем данные для записи в CSV
session_data = []
for session_key, data in sessions.items():
    session_data.append({
        'Session': f"{session_key}",
        'Source': session_key[0],  # Хост (192.168.179.201)
        'Destination': session_key[1],  # Сервер
        'Total_Packets': data['Source_Packets'] + data['Destination_Packets'],
        'Total_Length': data['Source_Length'] + data['Destination_Length'],
        'Source_Packets': data['Source_Packets'],
        'Source_Length': data['Source_Length'],
        'Destination_Packets': data['Destination_Packets'],
        'Destination_Length': data['Destination_Length']
    })

# Создаем DataFrame с результатами
output_df = pd.DataFrame(session_data)

# Сохраняем результат в новый CSV файл
output_csv_path = 'Detailed_session.csv'  # Укажите путь для сохранения файла
output_df.to_csv(output_csv_path, index=False)

print(f"Сессии успешно сформированы и сохранены в {output_csv_path}.")

