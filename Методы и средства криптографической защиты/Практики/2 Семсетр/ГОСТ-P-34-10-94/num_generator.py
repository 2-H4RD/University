
"""
num_generator.py

Реализация генерации параметров (p, q, a) для ГОСТ Р 34.10-94
по детерминистическому методу из статьи:

- p0 = p — большое простое (~512 бит),
- q = p1 — простое (~256 бит), делящее p-1,
- p строится через цепочку p_s, ..., p_1, p_0:
    t0 = t, t1 = floor(t0/2), ..., ts < 17;
    сначала генерируется случайное простое ps (~16 бит),
    затем для каждого i: p_{i-1} = p_i * N + 1,
    где N — чётное, и p_{i-1} проходит два условия:
        1) 2^{p_i * N} ≡ 1 (mod p_{i-1}),
        2) 2^{N}     ≠ 1 (mod p_{i-1}).

Также реализованы:
- собственный SHA-256 (для энтропии),
- LCG (линейный конгруэнтный генератор) как основной PRNG,
- тест Миллера–Рабина.
"""

import os
import time
import threading
from typing import List, Tuple

# ----------------------- SHA-256 (для энтропии) ----------------------- #

def sha256(data: bytes) -> bytes:
    """
    Полная ручная реализация SHA-256.
    Используется для перемешивания энтропии и получения 256-битных seed'ов.
    Возвращает 32 байта.
    """
    k = [
        0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
        0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
        0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
        0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
        0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
        0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
        0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
        0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
    ]

    h0 = 0x6a09e667
    h1 = 0xbb67ae85
    h2 = 0x3c6ef372
    h3 = 0xa54ff53a
    h4 = 0x510e527f
    h5 = 0x9b05688c
    h6 = 0x1f83d9ab
    h7 = 0x5be0cd19

    original_length = len(data) * 8
    data += b'\x80'
    while (len(data) * 8) % 512 != 448:
        data += b'\x00'
    data += original_length.to_bytes(8, byteorder='big')

    for i in range(0, len(data), 64):
        chunk = data[i:i+64]
        w = [int.from_bytes(chunk[j:j+4], 'big') for j in range(0, 64, 4)]
        for j in range(16, 64):
            s0 = ((w[j-15] >> 7) | (w[j-15] << 25)) ^ ((w[j-15] >> 18) | (w[j-15] << 14)) ^ (w[j-15] >> 3)
            s1 = ((w[j-2]  >> 17) | (w[j-2]  << 15)) ^ ((w[j-2]  >> 19) | (w[j-2]  << 13)) ^ (w[j-2] >> 10)
            w.append((w[j-16] + s0 + w[j-7] + s1) & 0xffffffff)

        a, b, c, d, e, f, g, h = h0, h1, h2, h3, h4, h5, h6, h7

        for j in range(64):
            S1 = ((e >> 6) | (e << 26)) ^ ((e >> 11) | (e << 21)) ^ ((e >> 25) | (e << 7))
            ch = (e & f) ^ ((~e) & g)
            temp1 = (h + S1 + ch + k[j] + w[j]) & 0xffffffff
            S0 = ((a >> 2) | (a << 30)) ^ ((a >> 13) | (a << 19)) ^ ((a >> 22) | (a << 10))
            maj = (a & b) ^ (a & c) ^ (b & c)
            temp2 = (S0 + maj) & 0xffffffff

            h, g, f, e, d, c, b, a = g, f, e, (d + temp1) & 0xffffffff, c, b, a, (temp1 + temp2) & 0xffffffff

        h0 = (h0 + a) & 0xffffffff
        h1 = (h1 + b) & 0xffffffff
        h2 = (h2 + c) & 0xffffffff
        h3 = (h3 + d) & 0xffffffff
        h4 = (h4 + e) & 0xffffffff
        h5 = (h5 + f) & 0xffffffff
        h6 = (h6 + g) & 0xffffffff
        h7 = (h7 + h) & 0xffffffff

    return (
        h0.to_bytes(4, 'big') + h1.to_bytes(4, 'big') +
        h2.to_bytes(4, 'big') + h3.to_bytes(4, 'big') +
        h4.to_bytes(4, 'big') + h5.to_bytes(4, 'big') +
        h6.to_bytes(4, 'big') + h7.to_bytes(4, 'big')
    )

# ----------------------- Сбор энтропии ----------------------- #

_counter = 0
_counter_lock = threading.Lock()

def get_entropy_sources() -> bytes:
    """
    Сбор энтропии:
    - текущее время (ns),
    - perf_counter,
    - process_time,
    - PID, PPID,
    - UID (если есть),
    - идентификатор потока,
    - счётчик вызовов.
    """
    parts = [
        str(time.time_ns()).encode(),
        str(time.perf_counter_ns()).encode(),
    ]

    if hasattr(time, "process_time_ns"):
        parts.append(str(time.process_time_ns()).encode())
    else:
        parts.append(str(int(time.process_time() * 1_000_000_000)).encode())

    parts.append(str(os.getpid()).encode())
    parts.append(str(os.getppid()).encode())

    if hasattr(os, "getuid"):
        parts.append(str(os.getuid()).encode())
    else:
        parts.append(b"0")

    parts.append(str(threading.get_ident()).encode())

    global _counter
    with _counter_lock:
        _counter = (_counter + 1) & 0xFFFFFFFFFFFFFFFF
        parts.append(str(_counter).encode())

    return b"|".join(parts)

def mix_entropy_with_hash(entropy: bytes, rounds: int = 4) -> bytes:
    """
    Многократное хэширование энтропии для «размазывания».
    Возвращает 32-байтовый (256-битный) блок.
    """
    acc = entropy
    for r in range(rounds):
        acc = sha256(acc + r.to_bytes(2, 'big') + acc[::-1])
    return acc

# ----------------------- Линейный конгруэнтный генератор (LCG) ----------------------- #

class LinearCongruentialGenerator:
    """
    Линейный конгруэнтный генератор на модуле m = 2^256.
    state_{n+1} = (a * state_n + c) mod m
    """

    def __init__(self, seed: int):
        self.m = 1 << 256
        # Константы a и c — большие нечётные числа.
        # Для учебных целей достаточно, криптостойкость не требуется.
        self.a = int(
            "5851F42D4C957F2D14057B7EF767814F"
            "26C34F5DF7C2340F1BBCDCB0F3E5A5F1", 16
        ) | 1
        self.c = int(
            "14057B7EF767814F5851F42D4C957F2D"
            "1F123BB5A1B3C9D7E3F4A5B6C7D8E9F", 16
        ) | 1
        self.state = seed % self.m

    def next(self) -> int:
        """
        Следующее 256-битное значение генератора.
        """
        self.state = (self.a * self.state + self.c) % self.m
        return self.state

# Инициализация глобального LCG (seed — 256 бит из энтропии)
_seed_bytes = mix_entropy_with_hash(get_entropy_sources(), 4)  # 32 байта
_seed_int = int.from_bytes(_seed_bytes, 'big')
_lcg = LinearCongruentialGenerator(_seed_int)

# ----------------------- Обёртки над LCG (random bits/int) ----------------------- #

def lcg_random_bits(bits: int) -> int:
    """
    Получить случайное целое с заданным количеством бит, используя LCG.
    Старший бит НЕ устанавливается автоматически.
    """
    if bits <= 0:
        raise ValueError("bits must be > 0")
    value = 0
    remaining = bits
    while remaining > 0:
        block = _lcg.next()  # 256 бит
        value = (value << 256) | block
        remaining -= 256
    value &= (1 << bits) - 1
    return value

def _randbelow(high: int) -> int:
    """
    Равномерное 0 <= r < high через LCG (rejection sampling).
    """
    if high <= 0:
        raise ValueError("high must be positive")
    bits = high.bit_length()
    mask = (1 << bits) - 1
    while True:
        r = lcg_random_bits(bits) & mask
        if r < high:
            return r

def secure_random_int(min_val: int, max_val: int) -> int:
    """
    Случайное целое в диапазоне [min_val, max_val] с использованием LCG.
    """
    if max_val < min_val:
        raise ValueError("max_val must be >= min_val")
    rng = max_val - min_val + 1
    return min_val + _randbelow(rng)

def secure_random_bits(bits: int) -> int:
    """
    Случайное целое с заданным числом бит на основе LCG.
    Старший бит выставляется в 1 (для гарантии битности).
    """
    if bits <= 0:
        raise ValueError("bits must be > 0")
    value = lcg_random_bits(bits)
    # принудительно установить старший бит
    value |= 1 << (bits - 1)
    return value

# ----------------------- Малые простые и отсечка ----------------------- #

def sieve_primes(limit: int) -> List[int]:
    if limit < 2:
        return []
    bs = bytearray(b"\x01") * (limit + 1)
    bs[0:2] = b"\x00\x00"
    p = 2
    while p * p <= limit:
        if bs[p]:
            step = p
            start = p * p
            bs[start:limit+1:step] = b"\x00" * ((limit - start)//step + 1)
        p += 1
    return [i for i in range(2, limit + 1) if bs[i]]

_SMALL_PRIMES = sieve_primes(10_000)

def has_small_divisor(n: int) -> bool:
    """
    Проверка делимости n на первые ~1k простых.
    """
    for p in _SMALL_PRIMES:
        if n == p:
            return False
        if n % p == 0:
            return True
    return False

# ----------------------- Миллер–Рабин ----------------------- #

def _decompose_n_minus_1(n: int) -> Tuple[int, int]:
    """
    Разложение n-1 = 2^s * d, d нечётное.
    """
    d = n - 1
    s = 0
    while (d & 1) == 0:
        d >>= 1
        s += 1
    return s, d

def _miller_rabin_round(n: int, a: int, s: int, d: int) -> bool:
    """
    Один раунд Миллера–Рабина. True = «вероятно простое» для основания a.
    """
    x = pow(a, d, n)
    if x == 1 or x == n - 1:
        return True
    for _ in range(s - 1):
        x = (x * x) % n
        if x == n - 1:
            return True
    return False

def miller_rabin_test(n: int, rounds: int = 20) -> bool:
    """
    Тест Миллера–Рабина.
    Основания a берутся через LCG.
    Кол-во раундов 20 достаточно для учебных задач и малых/средних битностей.
    """
    if n < 2:
        return False
    if n in (2, 3):
        return True
    if n % 2 == 0:
        return False

    # отсечка малыми простыми
    for p in _SMALL_PRIMES:
        if n == p:
            return True
        if n % p == 0:
            return False

    s, d = _decompose_n_minus_1(n)
    for _ in range(rounds):
        a = 2 + _randbelow(n - 3)  # 2..n-2
        if not _miller_rabin_round(n, a, s, d):
            return False
    return True

# ----------------------- Общая генерация простого (если вдруг нужна) ----------------------- #

def generate_prime(bits: int, mr_rounds: int = 20) -> int:
    """
    Генерация простого числа заданной битности с помощью:
    - secure_random_bits,
    - отсев дли делимости малыми простыми,
    - Миллер–Рабин.
    НЕ используется в ГОСТ-цепочке, но оставлена для совместимости.
    """
    if bits < 2:
        raise ValueError("bits must be >= 2")

    while True:
        n = secure_random_bits(bits) | 1  # нечётный

        if has_small_divisor(n):
            continue

        if miller_rabin_test(n, rounds=mr_rounds):
            return n

# ----------------------- ГОСТ-цепочка t_i ----------------------- #

def _build_t_chain(t0: int) -> List[int]:
    """
    ГОСТ, Процедура A, шаг 2:
    Вычисляем последовательность (t0, t1, ..., ts) по правилу:
      t0 = t,
      если t_i > 17, то t_{i+1} = floor(t_i / 2),
      если t_i <= 17, то s = i.

    Возвращаем список [t0, t1, ..., ts].
    """
    if t0 < 17:
        raise ValueError("t0 должно быть >= 17 бит")
    t = [t0]
    while t[-1] > 17:
        t.append(t[-1] // 2)
    # последний t_s <= 17
    return t


def _generate_small_prime(bits: int = 16) -> int:
    """
    'Исходное простое значение ps формируется путем случайного выбора
    числа размером менее 17 бит и проверкой на простоту методом
    пробного деления' (из теоретического описания).

    Здесь:
      - случайный кандидат получаем из secure_random_bits;
      - отсеиваем малые делители;
      - проверяем тестом Миллера–Рабина.

    Это стартовый p_s длины t_s (t_s <= 17).
    """
    if bits > 17:
        raise ValueError("Для начального простого ожидается t_s <= 17 бит.")
    while True:
        # случайный t_s-битный кандидат
        n = secure_random_bits(bits)
        n |= 1                 # делаем нечётным
        n |= 1 << (bits - 1)   # гарантируем старший бит = 1

        if has_small_divisor(n):
            continue
        if miller_rabin_test(n, rounds=10):
            return n

def _procedure_A_step(pi_plus_1: int,
                      t_m: int,
                      y0: int,
                      c_lcg: int) -> Tuple[int, int]:
    """
    Один уровень Процедуры A: по простому p_{m+1} строим p_m длины t_m.

    Вход:
      - pi_plus_1 = p_{m+1};
      - t_m       = t_m (битовая длина p_m), совпадает с t_chain[m];
      - y0        = текущее состояние линейного конгруэнтного датчика (y_0);
      - c_lcg     = параметр 'c' датчика (нечётное, 0 < c < 2^16).

    Выход:
      - p_m       = найденное простое p_m;
      - y0_next   = новое значение y_0 после шага (шаг 8: y0 := Y_m).

    Шаги со ссылками на ГОСТ:

      5) r_m = floor(t_m / 16)
      6) y_{i+1} = (19381 * y_i + c) mod 2^16, i = 0..r_m-1
      7) Y_m = sum_{i=0}^{r_m-1} y_{i+1} * 2^{16*i}
      8) y0 := Y_m
      9) N = floor(2^{t_m-1} / p_{m+1}) +
             floor((2^{t_m-1} * Y_m) / (p_{m+1} * 2^{16*r_m}))
         если N нечётно, N := N + 1
      10) k := 0
      11) p_m = p_{m+1} * (N + k) + 1
      12) если p_m > 2^{t_m}, перейти к шагу 6
      13) проверить:
             2^{p_{m+1}(N+k)}  ≡ 1 (mod p_m),
             2^{N+k}          ≠ 1 (mod p_m);
          если не выполнено: k := k + 2, перейти к шагу 11;
          иначе m := m - 1 (выход из этой функции).
    """
    MOD16 = 1 << 16
    q = pi_plus_1  # чтобы совпадало с теоремой: p = q * N + 1

    # --- шаг 5: r_m = floor(t_m / 16) ---
    r_m = t_m // 16
    if r_m <= 0:
        r_m = 1  # на всякий случай

    # Внешний цикл: реализует "если p_m > 2^{t_m}, перейти к шагу 6"
    while True:
        # --- шаг 6: последовательность (y_1, ..., y_{r_m}) по LCG ---
        y_i = y0 & 0xFFFF
        y_list = []
        for _ in range(r_m):
            # y_{i+1} = (19381 * y_i + c) mod 2^16
            y_i = (19381 * y_i + c_lcg) % MOD16
            y_list.append(y_i)

        # --- шаг 7: Y_m = sum_{i=0}^{r_m-1} y_{i+1} * 2^{16*i} ---
        Y_m = 0
        for i, val in enumerate(y_list):
            Y_m += val << (16 * i)

        # --- шаг 8: y0 := Y_m ---
        # В процедурной логике ГОСТа y0 хранит "слово", но LCG всегда
        # использует его по mod 2^16, поэтому в LCG мы будем использовать
        # y0_next = Y_m mod 2^16, а для формулы шага 9 сам Y_m используем целиком.
        y0_for_next_step = Y_m & 0xFFFF

        # --- шаг 9: N = floor(2^{t_m-1} / p_{m+1}) +
        #               floor((2^{t_m-1} * Y_m) / (p_{m+1} * 2^{16*r_m})) ---
        two_pow = 1 << (t_m - 1)  # 2^{t_m-1}
        # Первый член: floor(2^{t_m-1} / p_{m+1})
        term1 = two_pow // q
        # Второй член: floor( (2^{t_m-1} * Y_m) / (p_{m+1} * 2^{16*r_m}) )
        term2 = (two_pow * Y_m) // (q * (1 << (16 * r_m)))
        N = term1 + term2

        # Если N нечётно, N := N + 1
        if N % 2 == 1:
            N += 1

        # --- шаг 10: k := 0 ---
        k = 0

        # Внутренний цикл: шаги 11-13 (подбор k)
        while True:
            # --- шаг 11: p_m = p_{m+1} * (N + k) + 1 ---
            Nk = N + k
            p_m = q * Nk + 1

            # --- шаг 12: если p_m > 2^{t_m}, перейти к шагу 6 ---
            if p_m > (1 << t_m):
                # выходим из внутреннего цикла -> заново шаги 6-9 с новым Y_m
                break

            # --- шаг 13: проверка условий теоремы ---
            # 2^{p_{m+1}(N+k)} (mod p_m) == 1 ?
            cond1 = pow(2, q * Nk, p_m) == 1
            # 2^{N+k} (mod p_m) != 1 ?
            cond2 = pow(2, Nk, p_m) != 1

            if cond1 and cond2:
                # Условия выполнены — найдено подходящее p_m.
                return p_m, y0_for_next_step

            # Если хотя бы одно из условий не выполнено:
            # k := k + 2, и повторяем шаг 11
            k += 2

        # Если мы сюда попали, значит p_m > 2^{t_m}, переходим к шагу 6
        # с уже обновлённым y0 (y0 := Y_m).
        y0 = y0_for_next_step
        # Цикл while True начнётся заново: новые y_i, новый Y_m, новый N.


def generate_gost_pq(bits_p: int = 512,
                     bits_q: int = None,
                     x0: int = None,
                     c_lcg: int = None) -> Tuple[int, int]:
    """
    ГОСТ Р 34.10-94, Процедура A (модифицированная под Python):

    - Генерирует простое p длины t = bits_p бит,
    - с простым делителем q длины примерно floor(t/2) бит,
      где q = p_1 (второй элемент в цепочке p_s ... p_1, p_0).

    Параметры:
      bits_p  -- желаемая длина p (t >= 17).
      bits_q  -- ожидаемая длина q (необязательно, только для контроля/диагностики).
      x0      -- начальное состояние линейного конгруэнтного датчика (0 < x0 < 2^16).
      c_lcg   -- параметр c датчика (нечётный, 0 < c < 2^16).

    Если x0 или c_lcg не заданы, они выбираются случайно из энтропии.
    """

    # --- шаг 1: y0 := x0 ---
    MOD16 = 1 << 16
    if x0 is None:
        # по ГОСТу x0 задаёт пользователь; здесь для лабораторки берём из энтропии
        x0 = secure_random_int(1, MOD16 - 1)
    if c_lcg is None:
        # c должно быть нечётным и 0 < c < 2^16
        c_lcg = secure_random_int(1, MOD16 - 1)
        if c_lcg % 2 == 0:
            c_lcg ^= 1  # делаем нечётным

    y0 = x0 & 0xFFFF

    # --- шаг 2: вычислить последовательность (t0, t1, ..., ts) ---
    t_chain = _build_t_chain(bits_p)
    # t_chain: [t0, t1, ..., ts], последний <= 17
    s = len(t_chain) - 1  # индекс ts

    # --- шаг 3: найти исходное простое число p_s длины t_s ---
    t_s = t_chain[s]
    p_list: List[int] = [0] * (s + 1)
    p_list[s] = _generate_small_prime(bits=t_s)

    # --- шаг 4: m := s - 1 ---
    # И дальше реализуем шаги 5–14 в цикле по m от s-1 до 0.
    m = s - 1

    while m >= 0:
        t_m = t_chain[m]
        p_next = p_list[m + 1]   # p_{m+1}

        # Один уровень Процедуры A: шаги 5–13, получаем p_m и новый y0
        p_m, y0 = _procedure_A_step(pi_plus_1=p_next,
                                    t_m=t_m,
                                    y0=y0,
                                    c_lcg=c_lcg)

        p_list[m] = p_m

        # --- шаг 14: если m > 0, перейти к шагу 5 (следующий уровень),
        #             если m < 0, p0 и p1 — искомые p и q.
        m -= 1

    p = p_list[0]  # p0 — итоговое большое простое
    q = p_list[1]  # p1 — делитель p-1

    # Необязательная проверка длины q
    if bits_q is not None:
        # Это не критично, просто можно вывести в лог/print при отладке:
        # print(f"[DEBUG] bitlen(q) = {q.bit_length()}, ожидаемо около {bits_q}")
        pass

    return p, q

# ----------------------- Параметр a для ГОСТ 34.10-94 ----------------------- #

def generate_gost_a(p: int, q: int) -> int:
    """
    Генерация параметра a для ГОСТ Р 34.10-94:
      - p, q — уже сгенерированы так, что q | (p-1),
      - ищем a такое, что:
          a^q ≡ 1 (mod p),
          1 < a < p.

    Использует LCG для выбора базового h.
    """
    exp = (p - 1) // q
    while True:
        # h в [2, p-2]
        h = 2 + secure_random_int(0, p - 4)
        a = pow(h, exp, p)
        if 1 < a < p and pow(a, q, p) == 1:
            return a

# ----------------------- Демонстрация ----------------------- #

if __name__ == "__main__":
    print("=== Демонстрация ГОСТ-метода генерации (p, q, a) ===")

    bits_p = 512
    bits_q_expected = 256

    print(f"\n[1] Генерация пары (p, q) с p ≈ {bits_p} бит по ГОСТ-цепочке...")
    p, q = generate_gost_pq(bits_p=bits_p, bits_q=bits_q_expected)
    print(f"bitlen(p) = {p.bit_length()}")
    print(f"p = {p}")
    print(f"bitlen(q) = {q.bit_length()}")
    print(f"q = {q}")
    print(f"(p-1) % q = {(p - 1) % q}")

    print("\n[2] Генерация параметра a для (p, q)...")
    a = generate_gost_a(p, q)
    print(f"a^q mod p = {pow(a, q, p)} (ожидается 1)")
    print(f"a = {a}")