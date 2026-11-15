from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from filemanager.errors import FMError

# Explicit, recorded Argon2id settings; load-tested with bounded login concurrency.
HASHER = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=2)
DUMMY = HASHER.hash("dummy-account-never-authenticates")


def hash_password(password: str) -> str:
    if not isinstance(password, str) or not 15 <= len(password) <= 128:
        raise FMError("PASSWORD_LENGTH_15_128")
    return HASHER.hash(password)


def verify_password(encoded: str, password: str) -> bool:
    if not isinstance(password, str) or len(password) > 128:
        HASHER.verify(DUMMY, "dummy-account-never-authenticates")
        return False
    try:
        return HASHER.verify(encoded, password)
    except (VerificationError, InvalidHashError):
        return False

