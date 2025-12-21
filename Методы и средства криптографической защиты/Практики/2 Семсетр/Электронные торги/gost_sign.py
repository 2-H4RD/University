# -*- coding: utf-8 -*-
# gost_sign.py
#
# Реализация подписи и проверки подписи по ГОСТ Р 34.10-94
# Использует:
#   - num_generator.py    (p, q, a)
#   - gost_hash_3411.py   (hash)
#
# СОВМЕСТИМ с новым вариантом gost_hash_3411.py

from typing import Tuple
from num_generator import generate_gost_pq, generate_gost_a, secure_random_int
from gost_hash_3411 import gost_hash_3411 as _gost_hash
# ---------------------------------------------------------------------
#  Преобразование хэша из 32-байтового массива в число (big-endian)
# ---------------------------------------------------------------------

def hash_to_int(message: bytes) -> int:
    """Возвращает числовое значение хэша по ГОСТ 34.11-94."""
    H_be = _gost_hash(message)   # 32 байта MSB→LSB
    return int.from_bytes(H_be, byteorder="big")


# ---------------------------------------------------------------------
#  Генерация ключевой пары по ГОСТ Р 34.10-94
# ---------------------------------------------------------------------

def generate_keys() -> Tuple[int, int, int, int]:
    """
    Возвращает (p, q, a, x, y):

        p, q, a — параметры ГОСТ
        x       — закрытый ключ
        y = a^x mod p — открытый ключ
    """
    print("\n[ГОСТ] Генерация параметров p, q ...")
    p, q = generate_gost_pq(bits_p=512)

    print("[ГОСТ] Генерация параметра a ...")
    a = generate_gost_a(p, q)

    # приватный ключ x ∈ [1, q-1]
    x = secure_random_int(1, q - 1)
    # открытый ключ y = a^x mod p
    y = pow(a, x, p)

    print("[ГОСТ] ГОТОВО: ключи сгенерированы.")
    return p, q, a, x, y


# ---------------------------------------------------------------------
#  Подпись по ГОСТ 34.10-94
# ---------------------------------------------------------------------

def sign_message(message: bytes, p: int, q: int, a: int, x: int) -> Tuple[int, int]:
    """
    Генерирует подпись сообщения:
        r = (a^k mod p) mod q
        s = (k*h + x*r) mod q
    где k — случайное число [1 .. q-1]
    """
    h = hash_to_int(message)
    if h == 0:
        h = 1

    while True:
        k = secure_random_int(1, q - 1)
        r = pow(a, k, p) % q
        if r == 0:
            continue
        s = (k * h + x * r) % q
        if s == 0:
            continue
        return r, s


# ---------------------------------------------------------------------
#  Проверка подписи
# ---------------------------------------------------------------------

def verify_signature(message: bytes, r: int, s: int, p: int, q: int, a: int, y: int) -> bool:
    """
    Проверка:
        h = H(M)
        v = h^{q−2} mod q   — мультипликативная инверсия по теореме Ферма
        z1 = s * v mod q
        z2 = (q - r) * v mod q
        u = (a^z1 * y^z2 mod p) mod q
        подпись корректна <=> u == r
    """
    if not (0 < r < q and 0 < s < q):
        return False

    h = hash_to_int(message)
    if h == 0:
        h = 1

    v = pow(h, q - 2, q)        # обратный элемент h^{-1} mod q

    z1 = (s * v) % q
    z2 = ((q - r) * v) % q

    u = (pow(a, z1, p) * pow(y, z2, p)) % p
    u = u % q

    return (u == r)


# ---------------------------------------------------------------------
#  DEMO — выполняется только при запуске файла напрямую
# ---------------------------------------------------------------------

if __name__ == "__main__":
    print("=== ТЕСТ ГОСТ ПОДПИСИ ===")

    # 1. Генерация параметров и ключей
    p, q, a, x, y = generate_keys()

    print(f"\np = {p}")
    print(f"q = {q}")
    print(f"a = {a}")
    print(f"x (секретный) = {x}")
    print(f"y (открытый)  = {y}")

    # 2. Тестируем сообщение
    message = b"TEST MESSAGE"
    print(f"\nСообщение: {message!r}")

    # 3. Подписываем
    r, s = sign_message(message, p, q, a, x)
    print(f"Подпись: r={r}, s={s}")

    # 4. Проверяем подпись
    ok = verify_signature(message, r, s, p, q, a, y)
    print("\nПроверка подписи:", "OK" if ok else "FAIL")

    # 5. Проверим модификацию сообщения
    fake = b"TEST MESSAGF"
    ok2 = verify_signature(fake, r, s, p, q, a, y)
    print("Проверка на подмену:", "OK (должно FAIL)" if ok2 else "Корректно: подмена обнаружена.")
