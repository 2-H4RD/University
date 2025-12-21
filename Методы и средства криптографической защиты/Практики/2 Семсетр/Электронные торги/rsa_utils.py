# common/rsa_utils.py

"""
rsa_utils.py

Реализация RSA-аутентификации на основе простых чисел,
сгенерированных ГОСТ-процедурой A (через num_generator.py).

Использует:
    - generate_gost_pq(bits_p=512)  → первое простое p1
    - generate_gost_pq(bits_p=512)  → второе простое p2
      для построения RSA-модуля n ≈ 1024 бит.

Реализовано:
    - генерация ключей RSA (n, e, d)
    - шифрование / расшифрование
    - подпись / проверка подписи
"""

from num_generator import generate_gost_pq, secure_random_int


# ================================================================
# ВСПОМОГАТЕЛЬНЫЕ АЛГОРИТМЫ
# ================================================================

def egcd(a: int, b: int):
    """Расширенный алгоритм Евклида: возвращает (g, x, y) такие, что ax + by = g = gcd(a, b)."""
    if b == 0:
        return (a, 1, 0)
    g, x1, y1 = egcd(b, a % b)
    return (g, y1, x1 - (a // b) * y1)


def modinv(a: int, m: int) -> int:
    """Обратный элемент: возвращает x = a^{-1} mod m или бросает исключение."""
    g, x, y = egcd(a, m)
    if g != 1:
        raise ValueError(f"modinv: обратного элемента для a={a} по модулю m={m} не существует (gcd={g})")
    return x % m


def generate_two_gost_primes(bits_p: int = 512) -> tuple[int, int]:
    """
    Обёртка: дважды вызываем ГОСТ-процедуру generate_gost_pq, берём p0 из каждой.
    p1 и p2 используются только как источник двух разных простых.

    Возвращает (prime1, prime2).
    """
    print(f"[RSA] Генерация первого ГОСТ-простого p1 (≈{bits_p} бит)...")
    p1, q1 = generate_gost_pq(bits_p=bits_p)
    print(f"[RSA] Первый простое число p1 сгенерировано, bitlen(p1)={p1.bit_length()}")

    while True:
        print(f"[RSA] Генерация второго ГОСТ-простого p2 (≈{bits_p} бит)...")
        p2, q2 = generate_gost_pq(bits_p=bits_p)
        print(f"[RSA] Второй простое число p2 сгенерировано, bitlen(p2)={p2.bit_length()}")
        if p2 != p1:
            break
        print("[RSA][WARN] p2 совпало с p1, перегенерируем p2...")

    return p1, p2


# ================================================================
#     ГЕНЕРАЦИЯ КЛЮЧЕЙ RSA
# ================================================================

def generate_rsa_keys(bits_p: int = 512):
    """
    Генерация RSA-ключей:
        1) берём два ГОСТ-простых p и q размера 512 бит (p1, p2);
        2) считаем n = p1 * p2 (≈1024 бита);
        3) φ(n) = (p1-1)*(p2-1);
        4) выбираем e: gcd(e, φ(n)) = 1;
        5) d = e^{-1} mod φ(n).

    Возвращает:
        (n, e, d, p1, p2)
    """

    print("[RSA] === НАЧАЛО ГЕНЕРАЦИИ RSA-КЛЮЧЕЙ НА ГОСТ-ПРОСТЫХ ===")
    p, q = generate_two_gost_primes(bits_p)
    n = p * q
    phi = (p - 1) * (q - 1)

    # Выбор e
    attempts = 0
    while True:
        attempts += 1
        e = secure_random_int(2, phi - 1)
        g, _, _ = egcd(e, phi)
        if g == 1:
            break
        if attempts>100:
            print("[RSA] первышение лимита попыток генерации e. Сброс p,q")
            attempts=0
            p, q = generate_two_gost_primes(bits_p)
            n = p * q
            phi = (p - 1) * (q - 1)


    print("[RSA] Простые p и q готовы.")
    print(f"[RSA] bitlen(p) = {p.bit_length()}, bitlen(q) = {q.bit_length()}")
    print(f"[RSA] bitlen(n) = {n.bit_length()}")
    print("[RSA] Вычислено φ(n)")
    print(f"[RSA] Выбрано e={e}")

    # Вычисление d
    print("[RSA] Находим d = e^{-1} mod φ(n)...")
    d = modinv(e, phi)
    print("[RSA] d успешно вычислено.")

    print("[RSA] === ГЕНЕРАЦИЯ RSA-КЛЮЧЕЙ ЗАВЕРШЕНА ===")
    return n, e, d, p, q


# ================================================================
# RSA ОПЕРАЦИИ
# ================================================================

def rsa_encrypt(message: int, e: int, n: int) -> int:
    """Шифрование: c = m^e mod n"""
    return pow(message, e, n)


def rsa_decrypt(cipher: int, d: int, n: int) -> int:
    """Расшифрование: m = c^d mod n"""
    return pow(cipher, d, n)


def rsa_sign(message: int, d: int, n: int) -> int:
    """Подпись: s = m^d mod n"""
    return pow(message, d, n)


def rsa_verify(message: int, signature: int, e: int, n: int) -> bool:
    """Проверка подписи: s^e mod n == message ?"""
    return pow(signature, e, n) == message


# ================================================================
# ДЕМОНСТРАЦИЯ
# ================================================================

if __name__ == "__main__":
    print("\n=== ДЕМОНСТРАЦИЯ RSA НА ГОСТ-ПРОСТЫХ ===\n")

    n, e, d, p, q = generate_rsa_keys()

    print("\n[DEMO] Модуль n =", n)
    print("[DEMO] bitlen(n) =", n.bit_length())
    print("[DEMO] Открытый ключ (e, n) =", e, n)
    print("[DEMO] Закрытый ключ (d, n) =", d, n)

    msg = 123456789
    print(f"\n[DEMO] Проверка подписи для msg = {msg}")

    s = rsa_sign(msg, d, n)
    print("[DEMO] signature =", s)
    print("[DEMO] verify =", rsa_verify(msg, s, e, n))

    c = rsa_encrypt(msg, e, n)
    print("\n[DEMO] Зашифрованное сообщение:", c)
    print("[DEMO] Расшифровано обратно:", rsa_decrypt(c, d, n))

    print("\n=== RSA демонстрация завершена ===\n")
