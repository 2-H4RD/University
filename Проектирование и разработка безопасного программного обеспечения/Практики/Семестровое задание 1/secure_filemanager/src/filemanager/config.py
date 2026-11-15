import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL

from filemanager.errors import FMError
from filemanager.security.secrets import decode_secret

PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    db_host: str
    db_port: int
    db_name: str
    db_user: str
    db_password: str = field(repr=False)
    storage_root: Path
    max_file_bytes: int = 50 * 1024 * 1024
    max_total_zip_bytes: int = 200 * 1024 * 1024
    max_zip_files: int = 1000
    max_zip_ratio: int = 100
    user_quota_bytes: int = 1024 * 1024 * 1024
    session_seconds: int = 900
    worker_timeout: float = 10.0
    worker_memory_bytes: int = 768 * 1024 * 1024
    max_document_bytes: int = 2 * 1024 * 1024
    testing: bool = False
    max_user_files: int = 10000
    max_outbox_files: int = 1000

    @property
    def url(self) -> URL:
        return URL.create("postgresql+psycopg", username=self.db_user, password=self.db_password,
                          host=self.db_host, port=self.db_port, database=self.db_name)

    @classmethod
    def load(cls, env_file: str | Path = ".env") -> "Settings":
        # An explicit local file takes precedence; no accidental production/test mixing.
        path = Path(env_file)
        if not path.is_absolute():
            path = PROJECT_ROOT / path
        if not path.is_file():
            raise FMError("CONFIG_MISSING")
        load_dotenv(path, override=True)
        required = ["FM_DB_NAME", "FM_DB_USER", "FM_DB_PASSWORD", "FM_STORAGE_ROOT"]
        if any(not os.getenv(key) for key in required):
            raise FMError("CONFIG_MISSING")
        root = Path(os.environ["FM_STORAGE_ROOT"])
        if not root.is_absolute():
            root = PROJECT_ROOT / root
        values = {
            "db_host": os.getenv("FM_DB_HOST", "127.0.0.1"),
            "db_port": int(os.getenv("FM_DB_PORT", "5432")),
            "db_name": os.environ["FM_DB_NAME"], "db_user": os.environ["FM_DB_USER"],
            "db_password": decode_secret(os.environ["FM_DB_PASSWORD"]), "storage_root": root.absolute(),
            "testing": os.getenv("FM_TESTING", "false").lower() == "true",
        }
        for key, cast in [
            ("max_file_bytes", int), ("max_total_zip_bytes", int), ("max_zip_files", int),
            ("max_zip_ratio", int), ("user_quota_bytes", int), ("session_seconds", int),
            ("worker_timeout", float), ("worker_memory_bytes", int), ("max_document_bytes", int),
            ("max_user_files", int), ("max_outbox_files", int),
        ]:
            value = os.getenv("FM_" + key.upper())
            if value is not None:
                values[key] = cast(value)
        obj = cls(**values)
        if obj.db_host not in {"127.0.0.1", "::1", "localhost"}:
            raise FMError("REMOTE_DB_REQUIRES_TLS_DESIGN")
        # Reject the supplied administrative/default credentials at runtime.
        if obj.db_user == "postgres" or obj.db_password == "postgres":  # nosec B105
            raise FMError("ADMIN_DB_CREDENTIALS_FORBIDDEN")
        if any(getattr(obj, f) <= 0 for f in [
            "max_file_bytes", "max_total_zip_bytes", "max_zip_files", "max_zip_ratio",
            "user_quota_bytes", "session_seconds", "worker_timeout", "worker_memory_bytes",
            "max_document_bytes",
            "max_user_files", "max_outbox_files",
        ]):
            raise FMError("INVALID_LIMIT")
        if obj.testing and not obj.db_name.endswith("_test"):
            raise FMError("TEST_DATABASE_REQUIRED")
        return obj

