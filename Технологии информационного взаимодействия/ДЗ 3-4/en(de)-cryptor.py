import os
from filecmp import clear_cache
def clear_screen():
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')
def wait_enter():
    input('Нажмите Enter...')
def caesar_menu():
    while True:
        print('=== Алгоритм Цезаря ===')
        print('1 - Шифрование')
        print('2 - Дешифрование')
        print('0 - Назад')
        print('> ', end='')
        mode = -1
        mode = input()
        clear_screen()
        if mode == '0':
            return
        if mode == '1' or mode == '2':
            print('Введите текст (латиница): ', end='')
            text= ''
            text = input()
            print('Ключ (целое число): ', end='')
            key = int(input())
            shift = key % 26
            if shift < 0:
                shift = shift + 26
            result = ''
            i = 0
            while i < len(text):
                c = text[i]
                is_upper = False
                is_lower = False
                if c.isupper():
                    is_upper = True
                if c.islower():
                    is_lower = True
                if is_upper or is_lower:
                    base = 'a'
                    if is_upper:
                        base = 'A'
                    offset = ord(c) - ord(base)
                    new_offset = offset
                    if mode == '1':
                        new_offset = (offset + shift) % 26
                    if mode == '2':
                        new_offset = (offset + 26 - shift) % 26
                    result += chr(ord(base) + new_offset)
                else:
                    result += c
                i = i + 1
            clear_screen()
            if mode == '1':
                print('Режим: Шифрование (Caesar)')
            if mode == '2':
                print('Режим: Дешифрование (Caesar)')
            print('Ключ: ' + str(key))
            print('Входной текст: ' + text)
            print('Результат: ' + result)
            wait_enter()
            clear_screen()
        else:
            clear_screen()
def xor_menu():
    while True:
        print('=== Алгоритм XOR ===')
        print('1 - Шифрование')
        print('2 - Дешифрование')
        print('0 - Назад')
        print('> ', end='')
        mode = -1
        mode = input()
        clear_screen()
        if mode == '0':
            return
        if mode == '1' or mode == '2':
            text = ''
            print('Введите текст (латиница): ', end='')
            text = input()
            print('Ключ (один символ): ', end='')
            key = input()[0]
            result = ''
            i = 0
            while i < len(text):
                result += chr(ord(text[i]) ^ ord(key))
                i = i + 1
            clear_screen()
            if mode == '1':
                print('Режим: Шифрование (XOR)')
            if mode == '2':
                print('Режим: Дешифрование (XOR)')
            print('Ключ: ' + key)
            print('Входной текст: ' + text)
            print('Результат: ' + result)
            wait_enter()
            clear_screen()
        else:
            clear_screen()
def multialphabet_menu():
    while True:
        print('=== Многоалфавитная замена ===')
        print('1 - Шифрование')
        print('2 - Дешифрование')
        print('0 - Назад')
        print('> ', end='')
        mode = -1
        mode = input()
        clear_screen()
        if mode == '0':
            return
        if mode == '1' or mode == '2':
            shifts = [12, 5, 9, 21]
            text = ''
            print('Введите текст (латиница): ', end='')
            text = input()
            result = ''
            i = 0
            while i < len(text):
                c = text[i]
                is_upper = False
                is_lower = False
                if c.isupper():
                    is_upper = True
                if c.islower():
                    is_lower = True
                if is_upper or is_lower:
                    base = 'a'
                    if is_upper:
                        base = 'A'
                    offset = ord(c) - ord(base)
                    shift = shifts[i % 4]
                    if mode == '2':
                        shift = 26 - shift
                    new_offset = (offset + shift) % 26
                    result += chr(ord(base) + new_offset)
                else:
                    result += c
                i = i + 1
            clear_screen()
            if mode == '1':
                print('Режим: Шифрование (Многоалфавитная)')
            if mode == '2':
                print('Режим: Дешифрование (Многоалфавитная)')
            print('Ключ: фиксированный [12, 5, 9, 21]')
            print('Входной текст: ' + text)
            print('Результат: ' + result)
            wait_enter()
            clear_screen()
        else:
            clear_screen()
def transposition_menu():
    while True:
        print('=== Перестановка ===')
        print('1 - Шифрование')
        print('2 - Дешифрование')
        print('0 - Назад')
        print('> ', end='')
        mode = -1
        mode = input()
        clear_screen()
        if mode == '0':
            return
        if mode == '1' or mode == '2':
            block_size = 4
            perm = [3, 1, 2, 0]
            inv_perm = [0, 0, 0, 0]
            i = 0
            while i < block_size:
                pos = perm[i]
                inv_perm[pos] = i
                i = i + 1
            text = ''
            print('Введите текст (латиница): ', end='')
            text = input()
            result = ''
            length = len(text)
            j = 0
            while j < length:
                block = [' '] * block_size
                k = 0
                while k < block_size:
                    idx = j + k
                    if idx < length:
                        block[k] = text[idx]
                    k = k + 1
                m = 0
                while m < block_size:
                    if mode == '1':
                        pos = perm[m]
                        result += block[pos]
                    if mode == '2':
                        pos = inv_perm[m]
                        result += block[pos]
                    m = m + 1
                j = j + block_size
            clear_screen()
            if mode == '1':
                print('Режим: Шифрование (Перестановка)')
            if mode == '2':
                print('Режим: Дешифрование (Перестановка)')
            print('Ключ: фиксированный [3, 1, 2, 0]')
            print('Входной текст: ' + text)
            print('Результат: ' + result)
            wait_enter()
            clear_screen()
        else:
            clear_screen()
def vigenere_menu():
    while True:
        print('=== Виженер ===')
        print('1 - Шифрование')
        print('2 - Дешифрование')
        print('0 - Назад')
        print('> ', end='')
        mode= -1
        mode = input()
        clear_screen()
        if mode == '0':
            return
        if mode == '1' or mode == '2':
            text = ''
            print('Введите текст (латиница): ', end='')
            text = input()
            key = ''
            print('Ключевое слово (латиница): ', end='')
            key = input()
            if len(key) == 0:
                print('Ключ не может быть пустым!')
                wait_enter()
                clear_screen()
                continue
            result = ''
            key_len = len(key)
            key_pos = 0
            i = 0
            while i < len(text):
                c = text[i]
                is_upper = False
                is_lower = False
                if c.isupper():
                    is_upper = True
                if c.islower():
                    is_lower = True
                if is_upper or is_lower:
                    kch = key[key_pos % key_len]
                    base = 'A'
                    if is_lower:
                        base = 'a'
                    shift = ord(kch.upper()) - ord('A')
                    offset = ord(c) - ord(base)
                    new_offset = offset
                    if mode == '1':
                        new_offset = (offset + shift) % 26
                    if mode == '2':
                        new_offset = (offset + 26 - shift) % 26
                    result += chr(ord(base) + new_offset)
                    key_pos = key_pos + 1
                else:
                    result += c
                i = i + 1
            clear_screen()
            if mode == '1':
                print('Режим: Шифрование (Виженер)')
            if mode == '2':
                print('Режим: Дешифрование (Виженер)')
            print('Ключ: ' + key)
            print('Входной текст: ' + text)
            print('Результат: ' + result)
            wait_enter()
            clear_screen()
        else:
            clear_screen()
def build_playfair_table(key, table):
    used = [False] * 26
    seq = ''
    i = 0
    while i < len(key):
        c = key[i].upper()
        if c == 'J':
            c = 'I'
        if c >= 'A' and c <= 'Z':
            pos = ord(c) - ord('A')
            if used[pos] == False:
                used[pos] = True
                seq += c
        i = i + 1
    c2 = 'A'
    while c2 <= 'Z':
        if c2 != 'J':
            pos = ord(c2) - ord('A')
            if  used[pos] == False:
                used[pos] = True
                seq += c2
        c2 = chr(ord(c2) + 1)
    k = 0
    while k < 25:
        row = k // 5
        col = k % 5
        table[row][col] = seq[k]
        k = k + 1
def playfair_menu():
    while True:
        print('=== Плейфер ===')
        print('1 - Шифрование')
        print('2 - Дешифрование')
        print('0 - Назад')
        print('> ', end='')
        mode = -1
        mode = input()
        clear_screen()
        if mode == '0':
            return
        if mode == '1' or mode == '2':
            text = ''
            print('Введите текст (латиница): ', end='')
            text = input()
            key = ''
            print('Ключевое слово (латиница): ', end='')
            key = input()
            if len(key) == 0:
                print('Ключ не может быть пустым!')
                wait_enter()
                clear_screen()
                continue
            table = [[''] * 5 for _ in range(5)]
            pts = ''
            i = 0
            build_playfair_table(key, table)
            while i < len(text):
                c = text[i].upper()
                if c.isalpha() and 'A' <= c <= 'Z':
                    if c == 'J':
                        pts += 'I'
                    else:
                        pts += c
                i = i + 1
            result = ''
            length = len(pts)
            j = 0
            while j < length:
                a = pts[j]
                b = a
                if j + 1 < length:
                    b = pts[j + 1]
                else:
                    b = a
                if a == b:
                    b = 'X'
                ra = ca = rb = cb = r = 0
                while r < 5:
                    c = 0
                    while c < 5:
                        if table[r][c] == a:
                            ra = r
                            ca = c
                        if table[r][c] == b:
                            rb = r
                            cb = c
                        c = c + 1
                    r = r + 1
                if mode == '1':
                    if ra == rb:
                        result += table[ra][(ca + 1) % 5]
                        result += table[rb][(cb + 1) % 5]
                    elif ca == cb:
                        result += table[(ra + 1) % 5][ca]
                        result += table[(rb + 1) % 5][cb]
                    else:
                        result += table[ra][cb]
                        result += table[rb][ca]
                if mode == '2':
                    if ra == rb:
                        result += table[ra][(ca - 1) % 5]
                        result += table[rb][(cb - 1) % 5]
                    elif ca == cb:
                        result += table[(ra - 1) % 5][ca]
                        result += table[(rb - 1) % 5][cb]
                    else:
                        result += table[ra][cb]
                        result += table[rb][ca]
                if a == b:
                    j = j + 1
                else:
                    j = j + 2
            clear_screen()
            if mode == '1':
                print('Режим: Шифрование (Плейфер)')
            if mode == '2':
                print('Режим: Дешифрование (Плейфер)')
            print('Ключ: ' + key)
            print('Входной текст: ' + text)
            print('Результат: ' + result)
            wait_enter()
            clear_screen()
        else:
            clear_screen()
while True:
    print('Выберите алгоритм:')
    print('1 - Цезарь')
    print('2 - XOR')
    print('3 - Многоалфавитная замена')
    print('4 - Перестановка')
    print('5 - Виженер')
    print('6 - Плейфер')
    print('0 - Выход')
    print('> ', end='')
    alg = -1
    alg = input()
    clear_screen()
    if alg == '0':
        break
    elif alg == '1':
        caesar_menu()
    elif alg == '2':
            xor_menu()
    elif alg == '3':
          multialphabet_menu()
    elif alg == '4':
         transposition_menu()
    elif alg == '5':
          vigenere_menu()
    elif alg == '6':
        playfair_menu()
    else:
        clear_screen()