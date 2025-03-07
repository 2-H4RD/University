# Словарь для сопоставления английских слов с числами
NUMBERS = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19,
    "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90
}


def convert(words):
    words = words.lower().split()  # Удаление лишних пробелов и приведение к нижнему регистру

    if not words:
        raise ValueError("Ввод не должен быть пустым.")

    result = 0
    current = 0
    has_hundred = False  # Флаг наличия слова "hundred"

    previous_number_type = None  # Для отслеживания типа предыдущего числа (единицы, десятки, от 10 до 19)

    for word in words:
        # Проверяем, если слово не является допустимым числом или "hundred"
        if word not in NUMBERS and word != "hundred":
            raise ValueError(f"Некорректное слово: {word}")

        # Если слово "hundred", проверяем правильность его использования
        if word == "hundred":
            if current == 0 or has_hundred:
                raise ValueError(f"Некорректное использование 'hundred'.")
            current *= 100
            has_hundred = True
            result += current  # Добавляем сотни к результату
            current = 0  # Обнуляем текущий счетчик для обработки последующих чисел (десятков или единиц)
            previous_number_type = "hundred"
            continue

        number = NUMBERS[word]

        # Проверка на некорректные повторения чисел
        if previous_number_type == "units" and number < 10:
            raise ValueError(f"Нельзя использовать два одинаковых числа подряд: '{word}'.")

        # Логика для добавления чисел
        if number >= 10:  # Это десятки или числа от 10 до 19
            if previous_number_type == "tens":
                raise ValueError(f"Нельзя использовать два десятка подряд: '{word}'.")
            current += number
            previous_number_type = "tens" if number >= 20 else "teens"
        else:  # Это единицы
            if previous_number_type == "teens":
                raise ValueError(f"Нельзя использовать единицы после чисел от 10 до 19: '{word}'.")
            current += number
            previous_number_type = "units"

    # Добавляем оставшееся значение после завершения цикла
    result += current

    return result


def main():
    try:
        # Получаем ввод от пользователя
        input_str = input("Введите число прописью на английском (от 0 до 999): ")
        number = convert_to_number(input_str)
        print(f"Число: {number}")
    except ValueError as e:
        print(f"Ошибка: {e}")


if __name__ == "__main__":
    main()
