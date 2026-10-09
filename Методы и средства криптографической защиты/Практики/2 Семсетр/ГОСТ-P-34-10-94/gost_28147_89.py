from typing import List

# TEST S-BOXES (id-GostR3411-94-TestParamSet)
SBOX = [
    [4,10,9,2,13,8,0,14,6,11,1,12,7,15,5,3],
    [14,11,4,12,6,13,15,10,2,3,8,1,0,7,5,9],
    [5,8,1,13,10,3,4,2,14,15,12,7,6,0,9,11],
    [7,13,10,1,0,8,9,15,14,4,6,12,11,2,5,3],
    [6,12,7,1,5,15,13,8,4,10,9,14,0,3,11,2],
    [4,11,10,0,7,2,1,13,3,6,8,5,9,12,15,14],
    [13,11,4,1,3,15,5,9,0,10,14,7,6,8,2,12],
    [1,15,13,0,5,7,10,4,9,2,3,14,6,11,8,12],
]

def _rotl32(x: int, r: int) -> int:
    return ((x << r) & 0xFFFFFFFF) | (x >> (32 - r))

def _f(n1: int, k: int) -> int:
    x = (n1 + k) & 0xFFFFFFFF
    y = 0
    for i in range(8):  # S1 на младшем полубайте, S8 на старшем
        nib = (x >> (4 * i)) & 0xF
        s = SBOX[i][nib]
        y |= (s & 0xF) << (4 * i)
    return _rotl32(y, 11)

def magma_encrypt_block(block8_lehalves: bytes, key_words8_k1_to_k8: List[int]) -> bytes:
    """
    Шифрование 64-битного блока ГОСТ 28147-89 (Магма).
    Вход: 8 байт (LE-половины), 8 раундовых слов k1..k8 (32 бита).
    Выход: 8 байт в MSB-порядке (как печатают s[i] в ГОСТ 34.11-94 / RFC 5831).
    """
    assert len(block8_lehalves) == 8
    assert len(key_words8_k1_to_k8) == 8

    n1 = int.from_bytes(block8_lehalves[0:4], "little")
    n2 = int.from_bytes(block8_lehalves[4:8], "little")

    # 32 раунда: 1..24 идут k1..k8 повторно; 25..32 идут k8..k1;
    # последний раунд — без обмена половин.
    for r in range(24):
        k = key_words8_k1_to_k8[r % 8]
        t = n2 ^ _f(n1, k)
        n2, n1 = n1, t
    for r in range(8):
        k = key_words8_k1_to_k8[7 - r]
        if r < 7:
            t = n2 ^ _f(n1, k)
            n2, n1 = n1, t
        else:
            n2 = n2 ^ _f(n1, k)

    out_le = n1.to_bytes(4, "little") + n2.to_bytes(4, "little")
    return out_le[::-1]  # печатаем результат MSB-first (для удобства ГОСТ 34.11-94)
