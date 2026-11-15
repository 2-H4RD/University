import hashlib
import hmac
import json
import os
import shutil
from dataclasses import fields
from functools import wraps
from uuid import UUID, uuid4

import psutil
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from filemanager.audit.journal import Journal
from filemanager.errors import FMError
from filemanager.formats.worker import run
from filemanager.models import FileInfo
from filemanager.repositories.db import Database, execute, storage_lock
from filemanager.security.names import logical_name, name_key
from filemanager.services.auth import Auth
from filemanager.storage.objects import Storage
from filemanager.storage.safeio import pin_directory, reject_link


def audited(action, admin=False):
    def decorate(function):
        @wraps(function)
        def wrapper(self, *args, **kwargs):
            actor = None
            try:
                actor = self.auth.require(admin=admin)
                result = function(self, actor, *args, **kwargs)
                self.journal.verify()
                return result
            except FMError as exc:
                self.journal.event(action, actor=actor or self.auth.actor,
                                   outcome="failure", reason=exc.code)
                raise
            except IntegrityError as exc:
                self.journal.event(action, actor=actor, outcome="failure", reason="NAME_CONFLICT")
                raise FMError("NAME_CONFLICT") from exc
            except (SQLAlchemyError, OSError) as exc:
                # Fail closed; if audit DB is down this event may itself fail.
                try:
                    self.journal.event(action, actor=actor, outcome="failure", reason="OPERATION_FAILED")
                except SQLAlchemyError:
                    pass
                raise FMError("OPERATION_FAILED") from exc
        return wrapper
    return decorate


def file_info(row) -> FileInfo:
    data = dict(row)
    data["name"] = data.get("name", data.get("filename"))
    return FileInfo(**{field.name: data[field.name] for field in fields(FileInfo)})


def file_uuid(value):
    try:
        return UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise FMError("INVALID_FILE_ID") from exc


class Application:
    def __init__(self, settings):
        self.settings = settings
        self.db = Database(settings)
        self.storage = Storage(settings.storage_root, settings.max_file_bytes)
        self.journal = Journal(self.db, self.storage)
        self.auth = Auth(self.db, self.journal, settings)
        self.journal.verify()
        self._fault = None
        self._recover_system()

    def close(self):
        self.db.close()

    def _checkpoint_fault(self, point):
        if self.settings.testing and self._fault == "exit:" + point:
            os._exit(97)  # deterministic abrupt termination used only by integration tests
        if self.settings.testing and self._fault == point:
            raise RuntimeError("simulated process failure: " + point)

    def _get(self, conn, actor, file_id, lock=False):
        query = "SELECT * FROM fm.files WHERE id=:id AND owner_id=:owner AND NOT deleted"
        if lock:
            query += " FOR UPDATE"
        row = execute(conn, query, id=file_uuid(file_id), owner=actor.id).mappings().first()
        if row is None:
            # Do not distinguish foreign IDs from missing IDs.
            raise FMError("FILE_NOT_FOUND_OR_DENIED")
        return row

    def _bytes(self, row):
        data = self.storage.read(row["storage_key"])
        if len(data) != row["size"] or not hmac.compare_digest(
                hashlib.sha256(data).hexdigest(), row["sha256"]):
            raise FMError("FILE_INTEGRITY_FAILED")
        return data

    def _prepare(self, data: bytes, format: str):
        if not isinstance(data, bytes):
            raise FMError("BYTES_REQUIRED")
        if len(data) > self.settings.max_file_bytes:
            raise FMError("FILE_TOO_LARGE")
        if format in {"json", "xml"}:
            return run(format, data, self.settings)
        if format == "text":
            try:
                data.decode("utf-8", errors="strict")
            except UnicodeError as exc:
                raise FMError("INVALID_UTF8") from exc
        elif format not in {"binary", "zip"}:
            raise FMError("INVALID_FORMAT")
        return data

    def _quota(self, conn, actor, additional):
        size = execute(conn, "SELECT COALESCE(SUM(size),0) FROM fm.files "
                             "WHERE owner_id=:owner AND NOT deleted", owner=actor.id).scalar_one()
        exported, _ = self.storage.outbox_usage(actor.id)
        if size + exported + additional > self.settings.user_quota_bytes:
            raise FMError("USER_QUOTA_EXCEEDED")
        if shutil.disk_usage(self.storage.root).free < max(0, additional) + 64 * 1024 * 1024:
            raise FMError("DISK_SPACE_LOW")

    def _check_namespace(self, conn, actor, names, excluded=None):
        existing = execute(conn, "SELECT id,name_key FROM fm.files WHERE owner_id=:owner AND NOT deleted",
                           owner=actor.id).mappings()
        keys = {row["name_key"] for row in existing if row["id"] != excluded}
        for name in names:
            key = name_key(name)
            if key in keys:
                raise FMError("NAME_CONFLICT")
            keys.add(key)
        for key in keys:
            parts = key.split("/")
            if any("/".join(parts[:i]) in keys for i in range(1, len(parts))):
                raise FMError("NAME_CONFLICT")

    def _clean_locked(self, conn) -> int:
        referenced = set(execute(conn, "SELECT storage_key FROM fm.files WHERE NOT deleted").scalars())
        count = 0
        # Only flat, validated object keys are ever removed. No recursive deletion.
        for section in (self.storage.objects, self.storage.staging):
            with pin_directory(section):
                for path in section.iterdir():
                    reject_link(path)
                    if len(path.name) != 32:
                        raise FMError("UNEXPECTED_STORAGE_OBJECT")
                    if path.name not in referenced or section == self.storage.staging:
                        if section == self.storage.staging:
                            # A stale staging name must never remove a referenced object.
                            path.unlink()
                        else:
                            self.storage.remove(path.name)
                        count += 1
        execute(conn, "UPDATE fm.storage_jobs SET state='recovered' WHERE state='pending'")
        return count

    def _recover_system(self):
        with self.db.transaction() as conn:
            storage_lock(conn)
            count = self._clean_locked(conn)
            if count:
                self.journal.append(conn, "RECOVER", snapshot={"removed_objects": count})
        self.journal.verify()

    def _create_batch(self, actor, items, action):
        prepared = [(logical_name(name), self._prepare(data, fmt), fmt) for name, data, fmt in items]
        if not prepared:
            raise FMError("EMPTY_SELECTION")
        if len(prepared) > self.settings.max_zip_files:
            raise FMError("ZIP_TOO_MANY_FILES")
        keys = [uuid4().hex for _ in prepared]
        created = []
        with self.db.transaction() as conn:
            storage_lock(conn)
            self._clean_locked(conn)
            self._quota(conn, actor, sum(len(data) for _, data, _ in prepared))
            existing_count = execute(conn, "SELECT COUNT(*) FROM fm.files "
                                          "WHERE owner_id=:owner AND NOT deleted",
                                     owner=actor.id).scalar_one()
            if existing_count + len(prepared) > self.settings.max_user_files:
                raise FMError("USER_FILE_COUNT_LIMIT")
            self._check_namespace(conn, actor, [name for name, _, _ in prepared])
            job = uuid4()
            execute(conn, "INSERT INTO fm.storage_jobs(id,keys,state) VALUES (:id,CAST(:keys AS jsonb),'pending')",
                    id=job, keys=json.dumps(keys))
            for (name, data, fmt), key in zip(prepared, keys, strict=True):
                digest = self.storage.write(key, data)
                self._checkpoint_fault("after_publish")
                identifier = uuid4()
                row = execute(conn, """
                    INSERT INTO fm.files(id,owner_id,name,name_key,storage_key,size,sha256,format)
                    VALUES (:id,:owner,:name,:name_key,:key,:size,:sha,:format) RETURNING *
                """, id=identifier, owner=actor.id, name=name, name_key=name_key(name),
                    key=key, size=len(data), sha=digest, format=fmt).mappings().one()
                self._checkpoint_fault("after_metadata")
                self.journal.append(conn, action, actor=actor, file_id=identifier,
                                    snapshot={"name": name, "size": len(data), "version": 1})
                created.append(file_info(row))
            self._checkpoint_fault("after_audit")
            execute(conn, "UPDATE fm.storage_jobs SET state='done' WHERE id=:id", id=job)
        return created

    @audited("CREATE")
    def create(self, actor, name, data, format="text"):
        return self._create_batch(actor, [(name, data, format)], "CREATE")[0]

    @audited("LIST")
    def list_files(self, actor):
        with self.db.transaction() as conn:
            rows = execute(conn, "SELECT * FROM fm.files WHERE owner_id=:id AND NOT deleted ORDER BY name_key",
                           id=actor.id).mappings().all()
            self.journal.append(conn, "LIST", actor=actor)
        return [file_info(row) for row in rows]

    @audited("READ")
    def read(self, actor, file_id):
        with self.db.transaction() as conn:
            storage_lock(conn)
            row = self._get(conn, actor, file_id)
            data = self._bytes(row)
            self.journal.append(conn, "READ", actor=actor, file_id=row["id"],
                                snapshot={"version": row["version"]})
        return data

    @audited("MODIFY")
    def update(self, actor, file_id, data, expected_version):
        with self.db.transaction() as conn:
            storage_lock(conn)
            row = self._get(conn, actor, file_id, lock=True)
            if row["version"] != expected_version:
                raise FMError("VERSION_CONFLICT")
            data = self._prepare(data, row["format"])
            self._quota(conn, actor, len(data) - row["size"])
            key, job = uuid4().hex, uuid4()
            execute(conn, "INSERT INTO fm.storage_jobs(id,keys,state) VALUES (:id,CAST(:keys AS jsonb),'pending')",
                    id=job, keys=json.dumps([key]))
            digest = self.storage.write(key, data)
            self._checkpoint_fault("after_publish")
            updated = execute(conn, """
                UPDATE fm.files SET storage_key=:key,size=:size,sha256=:sha,version=version+1,
                  updated_at=clock_timestamp() WHERE id=:id RETURNING *
            """, key=key, size=len(data), sha=digest, id=row["id"]).mappings().one()
            self._checkpoint_fault("after_metadata")
            self.journal.append(conn, "MODIFY", actor=actor, file_id=row["id"],
                                snapshot={"name": row["name"], "version": updated["version"]})
            self._checkpoint_fault("after_audit")
            execute(conn, "UPDATE fm.storage_jobs SET state='done' WHERE id=:id", id=job)
        self._recover_system()
        return file_info(updated)

    @audited("DELETE")
    def delete(self, actor, file_id, expected_version):
        with self.db.transaction() as conn:
            storage_lock(conn)
            row = self._get(conn, actor, file_id, lock=True)
            if row["version"] != expected_version:
                raise FMError("VERSION_CONFLICT")
            execute(conn, "UPDATE fm.files SET deleted=TRUE,updated_at=clock_timestamp() WHERE id=:id",
                    id=row["id"])
            self.journal.append(conn, "DELETE", actor=actor, file_id=row["id"],
                                snapshot={"name": row["name"], "size": row["size"]})
            self._checkpoint_fault("after_metadata")
        self._recover_system()

    @audited("IMPORT")
    def import_file(self, actor, source_name, name=None, format="binary"):
        data = self.storage.read_import(actor.id, source_name)
        return self._create_batch(actor, [(name or source_name, data, format)], "IMPORT")[0]

    @audited("EXPORT")
    def export_file(self, actor, file_id, target_name):
        # The intent is durable before the physical write; completion is separate.
        with self.db.transaction() as conn:
            storage_lock(conn)
            row = self._get(conn, actor, file_id)
            data = self._bytes(row)
            self.journal.append(conn, "EXPORT_INTENT", actor=actor, file_id=row["id"])
        self.journal.verify()
        with self.db.transaction() as conn:
            storage_lock(conn)
            self._quota(conn, actor, len(data))
            if self.storage.outbox_usage(actor.id)[1] >= self.settings.max_outbox_files:
                raise FMError("OUTBOX_FILE_COUNT_LIMIT")
            path = self.storage.export(actor.id, target_name, data)
            self.journal.append(conn, "EXPORT", actor=actor, file_id=row["id"])
        return path

    @audited("ZIP_CREATE")
    def create_zip(self, actor, name, file_ids, password=None):
        ids = [file_uuid(identifier) for identifier in file_ids]
        if not ids or len(ids) > self.settings.max_zip_files:
            raise FMError("INVALID_SELECTION")
        contents = []
        with self.db.transaction() as conn:
            storage_lock(conn)
            total = 0
            for identifier in ids:
                row = self._get(conn, actor, identifier)
                total += row["size"]
                if total > self.settings.max_total_zip_bytes:
                    raise FMError("ZIP_TOTAL_LIMIT")
                contents.append((row["name"], self._bytes(row)))
            self.journal.append(conn, "ZIP_READ_SOURCE", actor=actor)
        self.journal.verify()
        data = run("zip_create", (contents, password), self.settings)
        return self._create_batch(actor, [(name, data, "zip")], "ZIP_CREATE")[0]

    @audited("ZIP_EXTRACT")
    def extract_zip(self, actor, file_id, prefix="extracted", password=None):
        prefix = logical_name(prefix)
        with self.db.transaction() as conn:
            storage_lock(conn)
            row = self._get(conn, actor, file_id)
            if row["format"] != "zip":
                raise FMError("ZIP_REQUIRED")
            data = self._bytes(row)
            self.journal.append(conn, "ZIP_READ_SOURCE", actor=actor, file_id=row["id"])
        self.journal.verify()
        entries = run("zip_extract", (data, password), self.settings)
        # Nested archives remain ordinary binary files: never recurse automatically.
        items = []
        for name, content in entries:
            suffix = name.rsplit(".", 1)[-1].lower()
            fmt = suffix if suffix in {"json", "xml"} else "binary"
            items.append((logical_name(prefix + "/" + name), content, fmt))
        return self._create_batch(actor, items, "ZIP_EXTRACT")

    @audited("DISKS")
    def disks(self, actor):
        result = []
        for disk in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(disk.mountpoint)
                result.append({"device": disk.device, "filesystem": disk.fstype,
                               "total": usage.total, "free": usage.free, "used": usage.used})
            except (PermissionError, OSError):
                continue
        self.journal.event("DISKS", actor=actor)
        return result

    @audited("LOCATIONS")
    def locations(self, actor):
        result = {section: str(self.storage.user_directory(section, actor.id))
                  for section in ("inbox", "outbox")}
        self.journal.event("LOCATIONS", actor=actor)
        return result

    @audited("AUDIT_READ", admin=True)
    def audit_events(self, actor, limit=50):
        if type(limit) is not int or not 1 <= limit <= 1000:
            raise FMError("INVALID_LIMIT")
        with self.db.transaction() as conn:
            rows = execute(conn, "SELECT payload FROM fm.operations ORDER BY id DESC LIMIT :limit",
                           limit=limit).scalars().all()
            self.journal.append(conn, "AUDIT_READ", actor=actor)
        return rows

    @audited("AUDIT_VERIFY", admin=True)
    def verify_audit(self, actor):
        count = self.journal.verify()
        self.journal.event("AUDIT_VERIFY", actor=actor)
        return count

    @audited("RECOVER", admin=True)
    def recover(self, actor):
        with self.db.transaction() as conn:
            storage_lock(conn)
            count = self._clean_locked(conn)
            self.journal.append(conn, "RECOVER", actor=actor, snapshot={"removed_objects": count})
        return count

    @audited("ACCOUNT_DISABLE", admin=True)
    def disable_user(self, actor, username):
        if username == actor.username:
            raise FMError("SELF_DISABLE_FORBIDDEN")
        with self.db.transaction() as conn:
            row = execute(conn, "UPDATE fm.users SET active=FALSE WHERE username=:name RETURNING id",
                          name=username).first()
            if not row:
                raise FMError("USER_NOT_FOUND")
            self.journal.append(conn, "ACCOUNT_DISABLE", actor=actor, snapshot={"target": str(row.id)})

