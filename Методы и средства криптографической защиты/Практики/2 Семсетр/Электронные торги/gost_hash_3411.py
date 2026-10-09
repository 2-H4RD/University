# -*- coding: utf-8 -*-
# gost_hash_3411.py
# ГОСТ Р 34.11-94 (с тестовым набором S-блоков). Многоблочная обработка.
# Шифр Магма вынесен в модуль common/gost_28147_89.py

from typing import List, Tuple
from gost_28147_89 import magma_encrypt_block

# ---------- Keygen (LE-модель) ----------

def _P_permutation(source32: bytes) -> List[int]:
    """32 байта -> 8 LE32 слов (столбцы i,i+8,i+16,i+24), затем [W7..W0]."""
    words = []
    for i in range(8):
        chunk = bytes([source32[i], source32[i+8], source32[i+16], source32[i+24]])
        words.append(int.from_bytes(chunk, "little"))
    return list(reversed(words))


def _A_transform_LE(Y: bytes) -> bytes:
    """A(Y) в нашей LE-вёрстке: [y1|y2|y3|y4] -> [y2|y3|y4|(y1 xor y2)]."""
    y1, y2, y3, y4 = Y[0:8], Y[8:16], Y[16:24], Y[24:32]
    y1_xor_y2 = bytes(a ^ b for a, b in zip(y1, y2))
    return y2 + y3 + y4 + y1_xor_y2


C2 = bytes(32)
C4 = bytes(32)
# C3 из стандарта, сдвинутая под нашу LE-модель
C3_LE = bytes.fromhex(
    "FF00FFFF000000FFFF0000FF00FFFF0000FF00FF00FF00FFFF00FF00FF00FF00"
)[::-1]


def _gen_keys(H_le: bytes, V_le: bytes) -> Tuple[List[int], List[int], List[int], List[int]]:
    """Генерация K1..K4 на LE-входах U=H_le, V=V_le."""
    U = H_le
    V = V_le

    W = bytes(a ^ b for a, b in zip(U, V))
    K1 = _P_permutation(W)

    U = _A_transform_LE(U)
    V = _A_transform_LE(_A_transform_LE(V))
    W = bytes(a ^ b for a, b in zip(U, V))
    K2 = _P_permutation(W)

    U = _A_transform_LE(U)
    U = bytes(a ^ b for a, b in zip(U, C3_LE))
    V = _A_transform_LE(_A_transform_LE(V))
    W = bytes(a ^ b for a, b in zip(U, V))
    K3 = _P_permutation(W)

    U = _A_transform_LE(U)
    V = _A_transform_LE(_A_transform_LE(V))
    W = bytes(a ^ b for a, b in zip(U, V))
    K4 = _P_permutation(W)

    return K1, K2, K3, K4


# ---------- PSI (RFC-вариант, MSB-first 16-битные слова) ----------

def _psi_once_rfc(x: bytes) -> bytes:
    assert len(x) == 32
    eta = [int.from_bytes(x[2*i:2*i+2], "big") for i in range(16)]
    t = eta[15] ^ eta[14] ^ eta[13] ^ eta[12] ^ eta[3] ^ eta[0]
    new_eta = [t] + eta[0:15]
    return b"".join(w.to_bytes(2, "big") for w in new_eta)


def _psi_n_rfc(x: bytes, n: int) -> bytes:
    for _ in range(n):
        x = _psi_once_rfc(x)
    return x


# ---------- Вспомогательная арифметика ----------

def _add_256_le(a: bytes, b: bytes) -> bytes:
    """LE-сложение по модулю 2^256 (для Σ)."""
    return (
        (int.from_bytes(a, "little") + int.from_bytes(b, "little")) & ((1 << 256) - 1)
    ).to_bytes(32, "little")


# ---------- χ(M,H) ----------

def _compress_dual(H_be: bytes, M_vec_be: bytes) -> bytes:
    """
    chi(M,H) при двух представлениях:
      - keygen:   U=H_le, V=M_le (LE-входы),
      - mixing:   M' = M_vec_be (MSB-first, как в стандарте).
    Разрезание H: H = h4||h3||h2||h1; в Магму подаём h[::-1] (LE-представление 64-бит).
    """
    # 1) keygen на LE-входах
    H_le = H_be[::-1]
    V_le = M_vec_be[::-1]
    K1, K2, K3, K4 = _gen_keys(H_le, V_le)

    # 2) H = h4||h3||h2||h1 (MSB-first)
    h1 = H_be[24:32]
    h2 = H_be[16:24]
    h3 = H_be[8:16]
    h4 = H_be[0:8]

    # ключи в порядке k1..k8
    K1_run = list(reversed(K1))
    K2_run = list(reversed(K2))
    K3_run = list(reversed(K3))
    K4_run = list(reversed(K4))

    # 3) шифруем части H; вход в Магму — LE-представление 64-битного блока: h[::-1]
    s1 = magma_encrypt_block(h1[::-1], K1_run)
    s2 = magma_encrypt_block(h2[::-1], K2_run)
    s3 = magma_encrypt_block(h3[::-1], K3_run)
    s4 = magma_encrypt_block(h4[::-1], K4_run)

    # S = s4||s3||s2||s1 (MSB-first)
    S = s4 + s3 + s2 + s1

    # 4) chi(M,H) = PSI^61( H xor PSI( M' xor PSI^12(S) ) )
    T = _psi_n_rfc(S, 12)
    T = bytes(a ^ b for a, b in zip(M_vec_be, T))
    T = _psi_n_rfc(T, 1)
    T = bytes(a ^ b for a, b in zip(H_be, T))
    H_out_be = _psi_n_rfc(T, 61)
    return H_out_be


# ---------- Полный хэш для произвольного сообщения ----------

def gost3411_94_full(message: bytes) -> bytes:
    """
    Возвращает H_be (вектор, MSB-first). Печатный дайджест = H_be[::-1].hex().upper()
    Алгоритм:
      1) поблочно по 32 байта (последний блок — нулевой допаддинг справа),
      2) χ(L, H) для L = |M| в битах (LE-256 -> MSB-first),
      3) χ(Σ, H) для Σ = сумма всех блоков как LE-256 (затем MSB-first).
    """
    H_be = bytes(32)        # H1 = 0^256 (MSB-first)
    sigma_le = bytes(32)    # Σ в LE

    # 1) сообщение по 32-байтным блокам, последний — pad нулями справа
    for off in range(0, len(message), 32):
        block = message[off:off+32]
        if len(block) < 32:
            block = block + b"\x00" * (32 - len(block))       # нулевой допаддинг справа
        M_vec_be = block[::-1]                                 # векторное представление
        H_be = _compress_dual(H_be, M_vec_be)
        sigma_le = _add_256_le(sigma_le, block)                # Σ как сумма LE-блоков

    # 2) χ(L, H) — L в битах как LE-256 -> MSB-first
    L_le = (len(message) * 8).to_bytes(32, "little")
    H_be = _compress_dual(H_be, L_le[::-1])

    # 3) χ(Σ, H) — Σ в LE -> MSB-first
    H_be = _compress_dual(H_be, sigma_le[::-1])

    return H_be


def gost3411_digest_hex(message: bytes) -> str:
    """
    Печатный дайджест ГОСТ: «младшие байты первыми» (little-endian строка байт),
    как в стандартных примерах.
    """
    H_be = gost3411_94_full(message)
    return H_be[::-1].hex().upper()


# ---------- УДОБНЫЕ ОБЁРТКИ ДЛЯ ИМПОРТА ИЗ ДРУГИХ МОДУЛЕЙ ----------

def gost3411_94(message: bytes) -> bytes:
    """
    Основная функция хэширования для импорта:

        from gost_hash_3411 import gost3411_94

    Возвращает байтовый хэш H_be (MSB-first, как в gost3411_94_full).
    Печатный дайджест можно получить как:
        gost3411_94(message)[::-1].hex().upper()
    """
    return gost3411_94_full(message)


# Для совместимости с разными именами импорта:
#   from gost_hash_3411 import gost_hash_3411
#   from gost_hash_3411 import gost_hash
gost_hash_3411 = gost3411_94
gost_hash = gost3411_94


# ---------- Самопроверка на наборе тест-векторов ----------

if __name__ == "__main__":
    vectors = [
        (
            "Suppose the original message has length = 50 bytes",
            "471ABA57A60A770D3A76130635C1FBEA4EF14DE51F78B4AE57DD893B62F55208",
        ),
        ("", "CE85B99CC46752FFFEE35CAB9A7B0278ABB4C2D2055CFF685AF4912C49490F8D"),
        ("a", "D42C539E367C66E9C88A801F6649349C21871B4344C6A573F849FDCE62F314DD"),
        ("abc", "F3134348C44FB1B2A277729E2285EBB5CB5E0F29C975BC753B70497C06A4D51D"),
        ("message digest", "AD4434ECB18F2C99B60CBE59EC3D2469582B65273F48DE72DB2FDE16A4889A4D"),
        (
            "The quick brown fox jumps over the lazy dog",
            "77B7FA410C9AC58A25F49BCA7D0468C9296529315EACA76BD1A10F376D1F4294",
        ),
        (
            "The quick brown fox jumps over the lazy cog",
            "A3EBC4DAAAB78B0BE131DAB5737A7F67E602670D543521319150D2E14EEEC445",
        ),
        # и наш 32-байтный пример:
        (
            "This is message, length=32 bytes",
            "B1C466D37519B82E8319819FF32595E047A28CB6F83EFF1C6916A815A637FFFA",
        ),
    ]

    all_ok = True
    for msg, expected in vectors:
        got = gost3411_digest_hex(msg.encode("utf-8"))
        ok = (got == expected)
        print(f'GOST("{msg}") = {got}   [{"OK" if ok else "FAIL"}]')
        if not ok:
            print("   expected:", expected)
            all_ok = False

    print("\nALL TESTS OK?", all_ok)
