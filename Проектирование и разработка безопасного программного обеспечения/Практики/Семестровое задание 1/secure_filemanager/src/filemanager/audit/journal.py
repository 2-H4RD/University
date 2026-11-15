import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from uuid import uuid4

from filemanager.errors import FMError
from filemanager.repositories.db import execute
from filemanager.storage.safeio import open_regular, pin_directory

ZERO = "0" * 64


def canonical(data: dict) -> bytes:
    return json.dumps(data, sort_keys=True, ensure_ascii=True, separators=(",", ":")).encode("ascii")


class Journal:
    def __init__(self, db, storage):
        self.db, self.storage = db, storage
        self.key = storage.load_secret("audit.key")
        self.checkpoint = storage.root / "secrets" / "audit.checkpoint"

    def sign(self, payload: dict, domain: bytes = b"audit") -> str:
        return hmac.new(self.key, b"SFM-v1:" + domain + b"\x00" + canonical(payload),
                        hashlib.sha256).hexdigest()

    def append(self, conn, action: str, actor=None, file_id=None,
               outcome="success", reason="OK", snapshot=None):
        execute(conn, "SELECT pg_advisory_xact_lock(73490102)")
        head = execute(conn, "SELECT seq, signature FROM fm.audit_head WHERE singleton").one()
        payload = {
            "seq": head.seq + 1, "previous_hmac": head.signature,
            "time": datetime.now(UTC).isoformat(), "request_id": str(uuid4()),
            "user_id": str(actor.id) if actor else None,
            "file_id": str(file_id) if file_id else None,
            "action": action, "outcome": outcome, "reason": reason, "snapshot": snapshot,
        }
        execute(conn, "SELECT fm.append_event(:seq, CAST(:data AS jsonb), :prev, :sig)",
                seq=payload["seq"], data=canonical(payload).decode("ascii"),
                prev=head.signature, sig=self.sign(payload))

    def event(self, action: str, **kwargs):
        with self.db.transaction() as conn:
            self.append(conn, action, **kwargs)
        self.verify()

    def _read_checkpoint(self):
        try:
            with open_regular(self.checkpoint) as stream:
                raw = stream.read(2049)
        except FileNotFoundError:
            return None
        if len(raw) > 2048:
            raise FMError("AUDIT_CHECKPOINT_INVALID")
        try:
            data = json.loads(raw)
            signature = data.pop("checkpoint_hmac")
            if not hmac.compare_digest(signature, self.sign(data, b"checkpoint")):
                raise ValueError
            if type(data["seq"]) is not int or data["seq"] < 0:
                raise ValueError
            return data
        except (ValueError, KeyError, TypeError) as exc:
            raise FMError("AUDIT_CHECKPOINT_INVALID") from exc

    def verify(self) -> int:
        # Same transaction-scoped lock as appends also serializes checkpoint updates.
        with self.db.transaction() as conn:
            execute(conn, "SELECT pg_advisory_xact_lock(73490102)")
            checkpoint = self._read_checkpoint()
            previous, seq = ZERO, 0
            checkpoint_seen = checkpoint is None or checkpoint["seq"] == 0
            if checkpoint and checkpoint["seq"] == 0 and checkpoint["signature"] != ZERO:
                raise FMError("AUDIT_TAMPERED")
            rows = execute(conn, "SELECT * FROM fm.operations ORDER BY id")
            for row in rows.mappings():
                seq += 1
                payload = row["payload"]
                if (row["id"] != seq or row["previous_hmac"] != previous
                        or payload.get("seq") != seq or payload.get("previous_hmac") != previous
                        or not hmac.compare_digest(row["hmac"], self.sign(payload))):
                    raise FMError("AUDIT_TAMPERED")
                for column in ("action", "outcome", "reason"):
                    if row[column] != payload[column]:
                        raise FMError("AUDIT_TAMPERED")
                for column in ("user_id", "file_id", "request_id"):
                    if (str(row[column]) if row[column] else None) != payload[column]:
                        raise FMError("AUDIT_TAMPERED")
                if row["occurred_at"] != datetime.fromisoformat(payload["time"]):
                    raise FMError("AUDIT_TAMPERED")
                previous = row["hmac"]
                if checkpoint and seq == checkpoint["seq"]:
                    if not hmac.compare_digest(previous, checkpoint["signature"]):
                        raise FMError("AUDIT_TAMPERED")
                    checkpoint_seen = True
            head = execute(conn, "SELECT seq, signature FROM fm.audit_head WHERE singleton").one()
            if checkpoint is None and head.seq:
                raise FMError("AUDIT_CHECKPOINT_MISSING")
            if head.seq != seq or head.signature != previous or not checkpoint_seen:
                raise FMError("AUDIT_TAMPERED")
            if checkpoint and checkpoint["seq"] > seq:
                raise FMError("AUDIT_TAMPERED")
            data = {"seq": seq, "signature": previous}
            data["checkpoint_hmac"] = self.sign(data, b"checkpoint")
            temporary = self.checkpoint.parent / (uuid4().hex + ".tmp")
            with open_regular(temporary, create=True) as stream:
                stream.write(canonical(data))
                stream.flush()
                os.fsync(stream.fileno())
            with pin_directory(self.checkpoint.parent):
                os.replace(temporary, self.checkpoint)
            return seq

