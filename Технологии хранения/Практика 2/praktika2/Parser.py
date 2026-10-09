import pandas as pd
import re
import geoip2.database
import ipaddress  # Для проверки формата IP-адресов

# Стандартные порты для разных протоколов
protocol_ports = {
    'TCP': 443,  # Default for TCP
    'TLSv1.2': 443,  # Default for TLSv1.2
    'TLSv1.3': 443,  # Default for TLSv1.3
    'UDP': 53,  # Default for UDP
    'DNS': 53,  # Default for DNS
    'HTTP': 80,  # Default for HTTP
    'QUIC': 443,  # Default for QUIC
    'SSLv2': 443,  # Default for SSLv2
    'SSDP': 1900,  # Default for SSDP
    'MDNS': 5353,  # Default for MDNS
    'ARP': None  # ARP does not use ports
}

# Чтение исходного CSV файла
input_csv_path = 'Capture.csv'  # Укажите путь к вашему исходному файлу
df = pd.read_csv(input_csv_path)


# Функция для извлечения портов из колонки Info
def extract_ports(info, protocol):
    # Шаблон для поиска портов в формате "source_port > destination_port"
    match = re.search(r'(\d+)  >  (\d+)', info)
    if match:
        return int(match.group(1)), int(match.group(2))  # Возвращаем найденные порты
    else:
        # Если портов нет, используем зарезервированные порты для данного протокола
        default_port = protocol_ports.get(protocol, None)
        return default_port, default_port


# Подключение к базе данных GeoLite2-Country для поиска информации о стране
reader = geoip2.database.Reader('GeoLite2-Country.mmdb')


# Функция для проверки валидности IP (IPv4 или IPv6)
def is_valid_ip(ip):
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


# Функция для получения страны по IP
def get_country(ip):
    if not is_valid_ip(ip):
        return 'Invalid IP'  # Если IP адрес невалидный

    try:
        response = reader.country(ip)
        return response.country.name
    except geoip2.errors.AddressNotFoundError:
        return 'Unknown Country'  # Если IP адрес локальный или не найден
    except Exception as e:
        # Обработка других исключений, чтобы не остановить процесс
        return f"Error: {str(e)}"


# Добавляем новые колонки для портов, источника и назначения
df['Source_Country'] = df['Source'].apply(get_country)
df['Destination_Country'] = df['Destination'].apply(get_country)

source_ports = []
destination_ports = []

# Проходим по каждой строке и извлекаем порты
for index, row in df.iterrows():
    info = row['Info']
    protocol = row['Protocol']
    src_port, dst_port = extract_ports(info, protocol)  # Извлекаем порты
    source_ports.append(src_port)
    destination_ports.append(dst_port)

# Добавляем порты в DataFrame
df['Source_Port'] = source_ports
df['Destination_Port'] = destination_ports

# Удаляем колонку Info, так как она больше не нужна
df.drop(columns=['Info'], inplace=True)

# Сохраняем результат в новый CSV файл
output_csv_path = 'Detailed_capture.csv'  # Укажите путь для сохранения файла
df.to_csv(output_csv_path, index=False)

print(f"Файл успешно обработан и сохранен в {output_csv_path}.")

