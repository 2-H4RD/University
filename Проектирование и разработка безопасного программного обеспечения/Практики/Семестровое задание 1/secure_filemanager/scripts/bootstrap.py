"""Provision only this project's two databases. No server-wide config changes."""
import getpass
import os
import secrets
import sys
from pathlib import Path

import psycopg
from psycopg import sql

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from filemanager.security.permissions import protect
from filemanager.security.secrets import encode_secret

ROOT = Path(__file__).resolve().parents[1]


def provision(admin_password, *, test=False):
    suffix = "_test" if test else ""
    dbname = "secure_filemanager" + suffix
    owner, migrator, app = ("fm_test_owner", "fm_test_migrator", "fm_test_app") if test else (
        "fm_owner", "fm_migrator", "fm_app")
    env_path = ROOT / (".env.test" if test else ".env")
    if env_path.exists():
        print(f"{env_path.name}: already configured; credentials preserved.")
        return
    app_pw, migration_pw = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    with psycopg.connect(host="127.0.0.1", port=5432, dbname="postgres", user="postgres",
                         password=admin_password, autocommit=True) as conn:
        conn.execute("SET password_encryption='scram-sha-256'")
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname=%s", (dbname,)).fetchone()
        roles = conn.execute("SELECT rolname FROM pg_roles WHERE rolname=ANY(%s)",
                             ([owner, migrator, app],)).fetchall()
        if exists or roles:
            raise RuntimeError("Project database/roles already exist without config; refusing to overwrite.")
        conn.execute(sql.SQL("CREATE ROLE {} NOLOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE").format(
            sql.Identifier(owner)))
        for name, pw in ((migrator, migration_pw), (app, app_pw)):
            conn.execute(sql.SQL("CREATE ROLE {} LOGIN NOINHERIT NOSUPERUSER NOCREATEDB "
                                "NOCREATEROLE NOREPLICATION NOBYPASSRLS PASSWORD {}").format(
                                    sql.Identifier(name), sql.Literal(pw)))
        conn.execute(sql.SQL("GRANT {} TO {}").format(sql.Identifier(owner), sql.Identifier(migrator)))
        conn.execute(sql.SQL("CREATE DATABASE {} OWNER {} ENCODING 'UTF8' TEMPLATE template0").format(
            sql.Identifier(dbname), sql.Identifier(owner)))
        conn.execute(sql.SQL("REVOKE ALL ON DATABASE {} FROM PUBLIC").format(sql.Identifier(dbname)))
        for name in (migrator, app):
            conn.execute(sql.SQL("GRANT CONNECT ON DATABASE {} TO {}").format(
                sql.Identifier(dbname), sql.Identifier(name)))
    storage = "test-var" if test else "var"
    data = (
        f"FM_DB_HOST=127.0.0.1\nFM_DB_PORT=5432\nFM_DB_NAME={dbname}\n"
        f"FM_DB_USER={app}\nFM_DB_PASSWORD={encode_secret(app_pw)}\nFM_MIGRATOR_USER={migrator}\n"
        f"FM_MIGRATOR_PASSWORD={encode_secret(migration_pw)}\nFM_OWNER_ROLE={owner}\n"
        f"FM_STORAGE_ROOT={storage}\nFM_TESTING={'true' if test else 'false'}\n"
    )
    with env_path.open("x", encoding="utf-8") as stream:
        stream.write(data)
    protect(env_path)
    print(f"Created {dbname}, roles and protected {env_path.name}.")


if __name__ == "__main__":
    password = os.environ.pop("FM_BOOTSTRAP_PASSWORD", None) or getpass.getpass("PostgreSQL postgres password: ")
    try:
        provision(password)
        provision(password, test=True)
    except Exception:  # noqa: BLE001 - never print an exception containing a bootstrap secret
        print("Bootstrap failed; inspect the database state before retrying. No secrets are printed.", file=sys.stderr)
        raise SystemExit(1)

