def find_max_consecutive_zeros(file_path):
    max_zeros = 0  # Для хранения максимальной длины последовательности нулевых байт
    current_zeros = 0  # Для подсчета текущей последовательности нулевых байт

    try:
        with open(file_path, 'rb') as f:
            # Читаем файл побайтово
            byte = f.read(1)
            while byte:
                if byte == b'\x00':  # Если байт равен нулю
                    current_zeros += 1  # Увеличиваем счетчик последовательных нулевых байт
                else:
                    # Если встретился ненулевой байт, проверяем максимальную длину и сбрасываем счетчик
                    if current_zeros > max_zeros:
                        max_zeros = current_zeros
                    current_zeros = 0
                byte = f.read(1)

            # Проверяем последний блок нулевых байт
            if current_zeros > max_zeros:
                max_zeros = current_zeros

        return max_zeros
    except FileNotFoundError:
        print(f"Ошибка: файл {file_path} не найден.")
        return None
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        return None


# Пример использования
file_path = 'wmplayer.exe'  # Укажите путь к вашему .exe файлу
max_zeros = find_max_consecutive_zeros(file_path)
if max_zeros is not None:
    print(f"Максимальная длина последовательности нулевых байт в файле {file_path}: {max_zeros}")
