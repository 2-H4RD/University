"""Windows-user-bound secrets, including on filesystems without persistent ACLs."""
import base64
import os

from filemanager.errors import FMError

MAGIC = b"SFM-DPAPI-1\n"
ENTROPY = b"university-secure-filemanager-v1"


def seal(data: bytes) -> bytes:
    if os.name != "nt":
        raise FMError("WINDOWS_DPAPI_REQUIRED")
    import win32crypt
    return MAGIC + win32crypt.CryptProtectData(data, "Secure File Manager", ENTROPY, None, None, 1)


def unseal(data: bytes) -> bytes:
    if not data.startswith(MAGIC) or len(data) > 8192:
        raise FMError("UNPROTECTED_OR_INVALID_SECRET")
    try:
        import win32crypt
        return win32crypt.CryptUnprotectData(data[len(MAGIC):], ENTROPY, None, None, 1)[1]
    except Exception as exc:
        raise FMError("SECRET_UNAVAILABLE_FOR_THIS_WINDOWS_USER") from exc


def encode_secret(value: str) -> str:
    return "DPAPI:" + base64.b64encode(seal(value.encode("utf-8"))).decode("ascii")


def decode_secret(value: str) -> str:
    if not value.startswith("DPAPI:"):
        raise FMError("UNPROTECTED_DATABASE_PASSWORD")
    try:
        raw = base64.b64decode(value[6:], validate=True)
        return unseal(raw).decode("utf-8")
    except (ValueError, UnicodeError) as exc:
        raise FMError("INVALID_PROTECTED_SECRET") from exc

