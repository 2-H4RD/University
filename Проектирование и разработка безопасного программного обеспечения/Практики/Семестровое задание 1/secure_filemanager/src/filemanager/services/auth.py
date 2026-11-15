import hashlib
import hmac
import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy.exc import IntegrityError

from filemanager.errors import FMError
from filemanager.models import Actor
from filemanager.repositories.db import execute
from filemanager.security.names import login_name
from filemanager.security.passwords import DUMMY, HASHER, hash_password, verify_password


class Auth:
    def __init__(self, db, journal, settings):
        self.db, self.journal, self.settings = db, journal, settings
        self.actor = None
        self.last_seen = 0.0

    def register(self, username: str, password: str, *, admin=False):
        # admin=True is only used by the separate trusted provisioning command.
        try:
            username = login_name(username)
            encoded = hash_password(password)
            actor = Actor(uuid4(), username, "admin" if admin else "user")
            with self.db.transaction() as conn:
                if admin:
                    execute(conn, "SELECT pg_advisory_xact_lock(73490104)")
                    if execute(conn, "SELECT EXISTS(SELECT 1 FROM fm.users WHERE role='admin')").scalar_one():
                        raise FMError("ADMIN_ALREADY_PROVISIONED")
                execute(conn, "INSERT INTO fm.users(id,username,password_hash,role) "
                              "VALUES (:id,:name,:hash,:role)", id=actor.id, name=username,
                        hash=encoded, role=actor.role)
                self.journal.append(conn, "REGISTER", actor=actor)
            self.journal.verify()
            return actor
        except IntegrityError as exc:
            self.journal.event("REGISTER", outcome="failure", reason="USERNAME_UNAVAILABLE")
            raise FMError("USERNAME_UNAVAILABLE") from exc
        except FMError as exc:
            self.journal.event("REGISTER", outcome="failure", reason=exc.code)
            raise

    def login(self, username: str, password: str):
        self.actor = None
        username = username.lower()
        # HMAC prevents a leaked throttle table from exposing guessed usernames.
        bucket = hmac.new(self.journal.key, b"SFM-v1:throttle\x00" + username.encode("utf-8")[:256],
                          hashlib.sha256).hexdigest()
        error = None
        actor = None
        with self.db.transaction() as conn:
            execute(conn, "SELECT pg_advisory_xact_lock(73490103)")
            now = datetime.now(UTC)
            execute(conn, "DELETE FROM fm.auth_attempts WHERE window_started < :cutoff",
                    cutoff=now - timedelta(days=1))
            global_count = execute(conn, "SELECT COALESCE(SUM(attempts),0) FROM fm.auth_attempts "
                                         "WHERE window_started > :since",
                                   since=now - timedelta(minutes=5)).scalar_one()
            if global_count >= 100:
                self.journal.append(conn, "LOGIN", outcome="failure", reason="LOGIN_RATE_LIMIT")
                # Commit the failure audit before returning the error.
                error = "LOGIN_RATE_LIMIT"
            else:
                error = None
            if error:
                conn.commit()
                self.journal.verify()
                raise FMError(error)
            execute(conn, """
                INSERT INTO fm.auth_attempts(name_key,attempts,window_started)
                VALUES (:key,0,:now) ON CONFLICT(name_key) DO NOTHING
            """, key=bucket, now=now)
            attempt = execute(conn, "SELECT * FROM fm.auth_attempts WHERE name_key=:key FOR UPDATE",
                              key=bucket).mappings().one()
            # Global budget also caps table growth via repeated distinct login names.
            recent = execute(conn, "SELECT COALESCE(SUM(attempts),0) FROM fm.auth_attempts "
                                   "WHERE window_started > :since",
                             since=now - timedelta(minutes=5)).scalar_one()
            blocked = (attempt["blocked_until"] and attempt["blocked_until"] > now) or recent >= 100
            user = execute(conn, "SELECT * FROM fm.users WHERE username=:name", name=username).mappings().first()
            encoded = user["password_hash"] if user else DUMMY
            valid = verify_password(encoded, password)
            if blocked:
                error = "LOGIN_RATE_LIMIT"
            elif not valid or not user or not user["active"]:
                error = "LOGIN_FAILED"
            if error:
                count = attempt["attempts"] + 1 if now - attempt["window_started"] < timedelta(minutes=5) else 1
                start = attempt["window_started"] if count > 1 else now
                execute(conn, "UPDATE fm.auth_attempts SET attempts=:n,window_started=:start,"
                              "blocked_until=:blocked WHERE name_key=:key",
                        n=count, start=start, blocked=now + timedelta(seconds=60) if count >= 5 else None,
                        key=bucket)
                self.journal.append(conn, "LOGIN", outcome="failure", reason=error)
            else:
                actor = Actor(user["id"], user["username"], user["role"], user["auth_version"])
                execute(conn, "UPDATE fm.auth_attempts SET attempts=0,window_started=:now,"
                              "blocked_until=NULL WHERE name_key=:key", now=now, key=bucket)
                if HASHER.check_needs_rehash(encoded):
                    execute(conn, "UPDATE fm.users SET password_hash=:hash WHERE id=:id",
                            hash=hash_password(password), id=actor.id)
                self.journal.append(conn, "LOGIN", actor=actor)
        self.journal.verify()
        if error:
            raise FMError(error)
        self.actor = actor
        self.last_seen = time.monotonic()
        return actor

    def require(self, admin=False) -> Actor:
        if self.actor is None:
            raise FMError("LOGIN_REQUIRED")
        if time.monotonic() - self.last_seen > self.settings.session_seconds:
            expired = self.actor
            self.actor = None
            self.journal.event("SESSION_EXPIRED", actor=expired)
            raise FMError("SESSION_EXPIRED")
        with self.db.transaction() as conn:
            user = execute(conn, "SELECT active,role,auth_version FROM fm.users WHERE id=:id",
                           id=self.actor.id).first()
        if not user or not user.active:
            self.actor = None
            raise FMError("ACCOUNT_DISABLED")
        if user.auth_version != self.actor.auth_version:
            expired = self.actor
            self.actor = None
            self.journal.event("SESSION_REVOKED", actor=expired)
            raise FMError("SESSION_REVOKED")
        if admin and user.role != "admin":
            raise FMError("ACCESS_DENIED")
        self.last_seen = time.monotonic()
        return Actor(self.actor.id, self.actor.username, user.role, user.auth_version)

    def change_password(self, old: str, new: str):
        actor = self.require()
        try:
            encoded = hash_password(new)
            with self.db.transaction() as conn:
                row = execute(conn, "SELECT password_hash,auth_version FROM fm.users WHERE id=:id FOR UPDATE",
                              id=actor.id).one()
                if not verify_password(row.password_hash, old):
                    raise FMError("PASSWORD_CHANGE_FAILED")
                execute(conn, "UPDATE fm.users SET password_hash=:hash,auth_version=auth_version+1 WHERE id=:id",
                        hash=encoded, id=actor.id)
                self.journal.append(conn, "PASSWORD_CHANGE", actor=actor)
            self.journal.verify()
            # All sessions, including this one, must authenticate again.
            self.actor = None
        except FMError as exc:
            self.journal.event("PASSWORD_CHANGE", actor=actor, outcome="failure", reason=exc.code)
            raise

    def logout(self):
        if self.actor:
            self.journal.event("LOGOUT", actor=self.actor)
        self.actor = None

