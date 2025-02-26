import struct
def create_bmp(file_size):
    # Размеры заголовков
    header_size = 54
    # Количество байт для данных пикселей
    pixel_data_size = file_size - header_size
    # Количество пикселей (по 3 байта на пиксель)
    pixel_count = pixel_data_size // 3
    # Размеры изображения (пока что будем фиксировать их как квадратное изображение)
    width = int(pixel_count ** 0.5)
    height = width
    # Паддинг, чтобы строка данных была кратна 4 байтам
    row_size = (width * 3 + 3) & (~3)
    data_size = row_size * height
    # Заголовок файла (14 байт)
    file_header = b'BM'
    file_header += struct.pack('<I', header_size + data_size)  # общий размер файла
    file_header += struct.pack('<HH', 0, 0)  # зарезервировано
    file_header += struct.pack('<I', header_size)  # смещение до данных изображения
    # Заголовок информации (DIB Header, 40 байт)
    dib_header = struct.pack('<I', 40)  # размер DIB заголовка
    dib_header += struct.pack('<I', width)  # ширина изображения
    dib_header += struct.pack('<I', height)  # высота изображения
    dib_header += struct.pack('<H', 1)  # количество цветовых плоскостей
    dib_header += struct.pack('<H', 24)  # количество бит на пиксель (24 бита = RGB)
    dib_header += struct.pack('<I', 0)  # тип сжатия (0 = без сжатия)
    dib_header += struct.pack('<I', data_size)  # размер данных изображения
    dib_header += struct.pack('<I', 0)  # горизонтальное разрешение
    dib_header += struct.pack('<I', 0)  # вертикальное разрешение
    dib_header += struct.pack('<I', 0)  # количество цветов в палитре
    dib_header += struct.pack('<I', 0)  # важные цвета (0 - не важно)
    # Данные изображения (pixel data)
    pixel_data = b''
    for i in range(pixel_count):
        # Чередующиеся чёрно-белые пиксели
        color = (255, 255, 255) if i % 2 == 0 else (0, 0, 0)  # чёрный и белый пиксели
        pixel_data += struct.pack('<BBB', *color)
    # Паддинг до 4 байтов в каждой строке
    pixel_data_padded = b''
    for y in range(height):
        row = pixel_data[y * width * 3: (y + 1) * width * 3]
        row += b'\x00' * (row_size - len(row))  # добавление padding
        pixel_data_padded += row
    # Составляем итоговый файл
    with open('image30000.bmp', 'wb') as f:
        f.write(file_header)
        f.write(dib_header)
        f.write(pixel_data_padded)

# Генерация BMP-файла
file_size = 30000 # Размер файла в байтах (включая заголовки)
create_bmp(file_size)
