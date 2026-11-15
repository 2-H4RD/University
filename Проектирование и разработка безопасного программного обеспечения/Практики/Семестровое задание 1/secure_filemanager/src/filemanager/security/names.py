import re
import unicodedata
from pathlib import PureWindowsPath

from filemanager.errors import FMError

RESERVED = {"CON", "PRN", "AUX", "NUL", "CLOCK$", "CONIN$", "CONOUT$"}
RESERVED |= {f"{p}{n}" for p in ("COM", "LPT") for n in "123456789¹²³"}
KEY = re.compile(r"^[0-9a-f]{32}$")


def logical_name(value: str, nested: bool = True) -> str:
    value = unicodedata.normalize("NFC", value)
    if not value or len(value) > 255 or any(unicodedata.category(c).startswith("C") for c in value):
        raise FMError("UNSAFE_NAME")
    if PureWindowsPath(value).drive or value.startswith(("/", "\\")) or "\\" in value:
        raise FMError("UNSAFE_NAME")
    parts = value.split("/")
    if not nested and len(parts) != 1:
        raise FMError("UNSAFE_NAME")
    for part in parts:
        if (not part or part in {".", ".."} or len(part) > 120 or part.endswith((".", " "))
                or any(c in part for c in '<>:"|?*')
                or part.split(".")[0].upper() in RESERVED):
            raise FMError("UNSAFE_NAME")
    return value


def name_key(name: str) -> str:
    return logical_name(name).casefold()


def storage_key(key: str) -> str:
    if not KEY.fullmatch(key):
        raise FMError("INVALID_STORAGE_KEY")
    return key


def login_name(value: str) -> str:
    value = value.lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9_.-]{2,31}", value):
        raise FMError("INVALID_USERNAME")
    return value


def terminal_safe(value: str) -> str:
    # Escape ANSI/OSC, control characters, bidi controls and embedded newlines.
    return "".join(c if not unicodedata.category(c).startswith("C")
                   else f"\\u{ord(c):04x}" for c in value)

