from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class Actor:
    id: UUID
    username: str
    role: str
    auth_version: int = 1


@dataclass(frozen=True)
class FileInfo:
    id: UUID
    name: str
    size: int
    format: str
    version: int
    created_at: datetime
    updated_at: datetime

