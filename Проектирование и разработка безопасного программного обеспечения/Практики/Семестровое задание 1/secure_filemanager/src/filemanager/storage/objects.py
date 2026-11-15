import hashlib
import os
from pathlib import Path
from uuid import uuid4

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from filemanager.errors import FMError
from filemanager.security.names import logical_name, storage_key
from filemanager.security.permissions import protect
from filemanager.security.secrets import seal, unseal
from filemanager.storage.safeio import open_regular, pin_directory, reject_link


class Storage:
    def __init__(self, root: Path, max_bytes: int):
        self.root = root.absolute()
        self.max_bytes = max_bytes
        self.root.mkdir(parents=True, exist_ok=True)
        reject_link(self.root)
        self.acl_supported = protect(self.root)
        for name in ("objects", "staging", "inbox", "outbox", "secrets"):
            path = self.root / name
            path.mkdir(exist_ok=True)
            reject_link(path)
            protect(path)
        self.objects = self.root / "objects"
        self.staging = self.root / "staging"
        self.data_key = self.load_secret("storage.key")

    def object_path(self, key: str) -> Path:
        return self.objects / storage_key(key)

    def write(self, key: str, data: bytes) -> str:
        storage_key(key)
        if len(data) > self.max_bytes:
            raise FMError("FILE_TOO_LARGE")
        stage = self.staging / key
        nonce = os.urandom(12)
        envelope = b"SFM1" + nonce + AESGCM(self.data_key).encrypt(
            nonce, data, b"secure-fm-object-v1:" + key.encode("ascii"))
        with open_regular(stage, create=True) as stream:
            stream.write(envelope)
            stream.flush()
            os.fsync(stream.fileno())
        with pin_directory(self.staging), pin_directory(self.objects):
            # Immutable UUID names. Windows rename refuses an existing destination.
            os.rename(stage, self.object_path(key))
        return hashlib.sha256(data).hexdigest()

    def read(self, key: str) -> bytes:
        try:
            with open_regular(self.object_path(key)) as stream:
                envelope = stream.read(self.max_bytes + 33)
        except FileNotFoundError as exc:
            raise FMError("OBJECT_MISSING") from exc
        if len(envelope) > self.max_bytes + 32:
            raise FMError("FILE_TOO_LARGE")
        if len(envelope) < 32 or not envelope.startswith(b"SFM1"):
            raise FMError("FILE_INTEGRITY_FAILED")
        try:
            data = AESGCM(self.data_key).decrypt(
                envelope[4:16], envelope[16:], b"secure-fm-object-v1:" + key.encode("ascii"))
        except InvalidTag as exc:
            raise FMError("FILE_INTEGRITY_FAILED") from exc
        return data

    def remove(self, key: str):
        for path in (self.object_path(key), self.staging / storage_key(key)):
            with pin_directory(path.parent):
                try:
                    reject_link(path)
                    path.unlink()
                except FileNotFoundError:
                    pass

    def outbox_usage(self, user_id) -> tuple[int, int]:
        path = self.user_directory("outbox", user_id)
        total, count = 0, 0
        with pin_directory(path):
            for entry in path.iterdir():
                reject_link(entry)
                if not entry.is_file():
                    raise FMError("UNEXPECTED_STORAGE_OBJECT")
                total += entry.stat().st_size
                count += 1
        return total, count

    def user_directory(self, section: str, user_id) -> Path:
        if section not in {"inbox", "outbox"}:
            raise FMError("INVALID_DIRECTORY")
        # UUID validation prevents an untrusted actor from choosing a path.
        from uuid import UUID
        user_id = UUID(str(user_id))
        path = self.root / section / user_id.hex
        with pin_directory(path.parent):
            path.mkdir(exist_ok=True)
            reject_link(path)
        return path

    def read_import(self, user_id, name: str) -> bytes:
        name = logical_name(name, nested=False)
        with open_regular(self.user_directory("inbox", user_id) / name) as stream:
            data = stream.read(self.max_bytes + 1)
        if len(data) > self.max_bytes:
            raise FMError("FILE_TOO_LARGE")
        return data

    def export(self, user_id, name: str, data: bytes) -> Path:
        name = logical_name(name, nested=False)
        target = self.user_directory("outbox", user_id) / name
        # Exclusive creation: a pre-existing path is never overwritten.
        with open_regular(target, create=True) as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return target

    def load_secret(self, name: str) -> bytes:
        path = self.root / "secrets" / logical_name(name, nested=False)
        try:
            with open_regular(path) as stream:
                data = stream.read(8193)
        except FileNotFoundError:
            if name == "storage.key" and any(self.objects.iterdir()):
                raise FMError("STORAGE_KEY_MISSING")
            try:
                with open_regular(path, create=True) as stream:
                    stream.write(seal(os.urandom(32)))
            except (FileExistsError, OSError):
                # Another process may have initialized the same secret.
                if not path.exists():
                    raise
            with open_regular(path) as stream:
                data = stream.read(8193)
        data = unseal(data)
        if len(data) != 32:
            raise FMError("INVALID_SECRET")
        protect(path)
        return data

    def temporary_key(self) -> str:
        return uuid4().hex

