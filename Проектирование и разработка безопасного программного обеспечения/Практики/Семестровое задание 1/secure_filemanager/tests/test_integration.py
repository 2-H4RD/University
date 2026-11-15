import os
import stat
import subprocess
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from io import BytesIO
from uuid import uuid4

import pytest
from conftest import PASSWORD
from sqlalchemy.exc import DBAPIError

from filemanager.errors import FMError
from filemanager.formats.worker import run
from filemanager.repositories.db import execute
from filemanager.security.passwords import verify_password
from filemanager.services.application import Application
from filemanager.storage.safeio import open_regular

pytestmark = pytest.mark.integration


def fails(code, fn, *args, **kwargs):
    with pytest.raises(FMError) as caught:
        fn(*args, **kwargs)
    assert caught.value.code == code


def archive(entries):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as out:
        for name, data in entries:
            out.writestr(name, data)
    return stream.getvalue()


def test_real_postgresql_restricted_role(app):
    with app.db.transaction() as conn:
        assert execute(conn, "SHOW server_version").scalar_one().startswith("16.")
        row = execute(conn, "SELECT rolsuper,rolcreatedb,rolcreaterole FROM pg_roles "
                            "WHERE rolname=current_user").one()
        assert row == (False, False, False)
    for statement in [
        "DELETE FROM fm.operations", "UPDATE fm.audit_head SET seq=0",
        "TRUNCATE fm.operations", "CREATE TABLE fm.unauthorized(id INT)",
        "CREATE TABLE public.unauthorized(id INT)", "SET ROLE fm_test_owner",
        "INSERT INTO fm.operations(id) VALUES (999)",
    ]:
        with pytest.raises(DBAPIError), app.db.transaction() as conn:
            conn.exec_driver_sql(statement)


def test_foreign_keys_constraints(app):
    with pytest.raises(DBAPIError), app.db.transaction() as conn:
        execute(conn, "INSERT INTO fm.files(id,owner_id,name,name_key,storage_key,size,sha256,format) "
                      "VALUES (:id,:owner,'a','a',:key,1,:sha,'text')",
                id=uuid4(), owner=uuid4(), key=uuid4().hex, sha="0" * 64)


def test_auth_password_hash_and_sql_injection(app):
    user = app.auth.register("alice", PASSWORD)
    with app.db.transaction() as conn:
        encoded = execute(conn, "SELECT password_hash FROM fm.users WHERE id=:id", id=user.id).scalar_one()
    assert encoded.startswith("$argon2id$")
    assert PASSWORD not in encoded
    assert verify_password(encoded, PASSWORD)
    fails("LOGIN_FAILED", app.auth.login, "' OR 1=1; --", PASSWORD)
    fails("LOGIN_FAILED", app.auth.login, "alice", "incorrect-password")
    fails("LOGIN_REQUIRED", app.list_files)
    app.auth.login("alice", PASSWORD)
    info = app.create("quote' ; DROP TABLE users;--.txt", b"safe")
    assert app.read(info.id) == b"safe"
    assert app.journal.verify() >= 6


def test_salts_and_registration_failures(app):
    alice = app.auth.register("alice", PASSWORD)
    bob = app.auth.register("bobby", PASSWORD)
    with app.db.transaction() as conn:
        hashes = list(execute(conn, "SELECT password_hash FROM fm.users").scalars())
    assert len(set(hashes)) == 2
    fails("USERNAME_UNAVAILABLE", app.auth.register, "ALICE", PASSWORD)
    fails("PASSWORD_LENGTH_15_128", app.auth.register, "short", "short")
    fails("INVALID_USERNAME", app.auth.register, "../admin", PASSWORD)
    assert alice.id != bob.id


def test_admin_provisioning_once(app):
    app.auth.register("admin", PASSWORD, admin=True)
    fails("ADMIN_ALREADY_PROVISIONED", app.auth.register, "admin2", PASSWORD, admin=True)


def test_login_rate_limit(app):
    app.auth.register("alice", PASSWORD)
    for _ in range(5):
        fails("LOGIN_FAILED", app.auth.login, "alice", "bad")
    fails("LOGIN_RATE_LIMIT", app.auth.login, "alice", PASSWORD)
    assert app.auth.actor is None


def test_sessions_and_admin_access(app, alice):
    fails("ACCESS_DENIED", app.audit_events)
    app.auth.last_seen = time.monotonic() - app.settings.session_seconds - 1
    fails("SESSION_EXPIRED", app.list_files)
    app.auth.login("alice", PASSWORD)
    app.auth.logout()
    fails("LOGIN_REQUIRED", app.list_files)


def test_disable_revokes_existing_session(app, alice):
    app.auth.register("admin", PASSWORD, admin=True)
    second = Application(app.settings)
    try:
        second.auth.login("admin", PASSWORD)
        second.disable_user("alice")
        fails("ACCOUNT_DISABLED", app.list_files)
        fails("LOGIN_FAILED", app.auth.login, "alice", PASSWORD)
        fails("SELF_DISABLE_FORBIDDEN", second.disable_user, "admin")
    finally:
        second.close()


def test_crud_versions_metadata_and_audit(app, alice):
    info = app.create("hello.txt", "Привет".encode())
    assert info.version == 1
    assert app.read(info.id).decode() == "Привет"
    changed = app.update(info.id, b"updated", expected_version=1)
    assert changed.version == 2
    assert changed.size == 7
    fails("VERSION_CONFLICT", app.update, info.id, b"lost update", 1)
    fails("VERSION_CONFLICT", app.delete, info.id, 1)
    app.delete(info.id, 2)
    assert app.list_files() == []
    fails("FILE_NOT_FOUND_OR_DENIED", app.read, info.id)
    with app.db.transaction() as conn:
        assert execute(conn, "SELECT deleted FROM fm.files WHERE id=:id", id=info.id).scalar_one()
        actions = list(execute(conn, "SELECT action FROM fm.operations WHERE file_id=:id ORDER BY id",
                               id=info.id).scalars())
    assert actions == ["CREATE", "READ", "MODIFY", "DELETE"]
    assert not list(app.storage.objects.iterdir())


def test_foreign_file_access(app, alice):
    info = app.create("private.txt", b"private")
    app.auth.register("bobby", PASSWORD)
    app.auth.login("bobby", PASSWORD)
    fails("FILE_NOT_FOUND_OR_DENIED", app.read, info.id)
    fails("FILE_NOT_FOUND_OR_DENIED", app.update, info.id, b"overwrite", 1)
    fails("FILE_NOT_FOUND_OR_DENIED", app.delete, info.id, 1)
    fails("FILE_NOT_FOUND_OR_DENIED", app.create_zip, "stolen.zip", [info.id])
    fails("FILE_NOT_FOUND_OR_DENIED", app.export_file, info.id, "stolen.txt")
    assert app.list_files() == []


def test_namespace_collisions(app, alice):
    app.create("Folder/file.txt", b"a")
    fails("NAME_CONFLICT", app.create, "folder/FILE.TXT", b"b")
    fails("NAME_CONFLICT", app.create, "folder", b"c")
    app.create("other", b"d")
    fails("NAME_CONFLICT", app.create, "other/nested", b"e")


def test_quota_and_size(app, alice):
    app.settings = replace(app.settings, user_quota_bytes=10)
    app.create("one", b"12345678")
    fails("USER_QUOTA_EXCEEDED", app.create, "two", b"123")
    app.settings = replace(app.settings, max_file_bytes=2)
    fails("FILE_TOO_LARGE", app.create, "big", b"123")


def test_import_export_locations(app, alice):
    locations = app.locations()
    from pathlib import Path
    inbox, outbox = Path(locations["inbox"]), Path(locations["outbox"])
    (inbox / "input.bin").write_bytes(b"\x00\xffbinary")
    info = app.import_file("input.bin")
    path = app.export_file(info.id, "output.bin")
    assert path.parent == outbox
    assert path.read_bytes() == b"\x00\xffbinary"
    fails("OPERATION_FAILED", app.export_file, info.id, "output.bin")
    fails("UNSAFE_NAME", app.import_file, "../input.bin")
    assert app.disks()


def test_content_integrity(app, alice):
    info = app.create("data", b"authentic")
    with app.db.transaction() as conn:
        key = execute(conn, "SELECT storage_key FROM fm.files WHERE id=:id", id=info.id).scalar_one()
    app.storage.object_path(key).write_bytes(b"tampered")
    fails("FILE_INTEGRITY_FAILED", app.read, info.id)


@pytest.mark.parametrize("fmt,raw", [
    ("json", b'{"message":"hello","items":[1,2]}'),
    ("xml", b'<data><message>hello</message></data>'),
])
def test_documents_roundtrip(app, alice, fmt, raw):
    info = app.create("data." + fmt, raw, fmt)
    content = app.read(info.id)
    assert b"hello" in content
    assert info.format == fmt


@pytest.mark.parametrize("raw,code", [
    (b'{"x":1,"x":2}', "JSON_DUPLICATE_KEY"),
    (b'{"x":NaN}', "JSON_NONFINITE"),
    (b'{"x":1e999}', "JSON_NONFINITE"),
    (b'{bad}', "INVALID_JSON"),
    (b'"scalar"', "JSON_OBJECT_OR_ARRAY_REQUIRED"),
    (b"[" * 40 + b"0" + b"]" * 40, "DOCUMENT_COMPLEXITY_LIMIT"),
])
def test_malicious_json(app, alice, raw, code):
    fails(code, app.create, "evil.json", raw, "json")
    assert app.list_files() == []


@pytest.mark.parametrize("raw", [
    b'<!DOCTYPE data [<!ENTITY xxe SYSTEM "file:///C:/Windows/win.ini">]><data>&xxe;</data>',
    b'<!DOCTYPE data SYSTEM "http://127.0.0.1:9/no-network"><data/>',
    b'<!DOCTYPE a [<!ENTITY x "a"><!ENTITY y "&x;&x;&x;&x;">]><a>&y;</a>',
    b"<unclosed>",
])
def test_xxe_dtd_and_xml_bombs(app, alice, raw):
    fails("INVALID_XML", app.create, "evil.xml", raw, "xml")


def test_xml_xinclude_depth_and_input_limit(app, alice):
    fails("XML_XINCLUDE_FORBIDDEN", app.create, "evil.xml",
          b'<root xmlns:xi="http://www.w3.org/2001/XInclude"><xi:include href="file:///x"/></root>', "xml")
    fails("DOCUMENT_COMPLEXITY_LIMIT", app.create, "deep.xml", b"<a>" * 40 + b"</a>" * 40, "xml")
    app.settings = replace(app.settings, max_document_bytes=8)
    fails("DOCUMENT_TOO_LARGE", app.create, "big.json", b'{"long":"value"}', "json")


def test_worker_os_limits_and_timeout(settings):
    fails("WORKER_TIMEOUT", run, "_timeout_test", None, replace(settings, worker_timeout=0.3))
    fails("WORKER_MEMORY_LIMIT", run, "_memory_test", None,
          replace(settings, worker_memory_bytes=128 * 1024 * 1024))


def test_zip_and_aes_roundtrip(app, alice):
    text_file = app.create("docs/readme.txt", b"hello")
    json_file = app.create("data.json", b'{"hello":true}', "json")
    for encrypted in (False, True):
        password = PASSWORD if encrypted else None
        zipped = app.create_zip("secure.zip" if encrypted else "normal.zip",
                                [text_file.id, json_file.id], password=password)
        extracted = app.extract_zip(zipped.id, "aes" if encrypted else "normal", password=password)
        assert len(extracted) == 2
        assert any(app.read(item.id) == b"hello" for item in extracted)
        if encrypted:
            fails("INVALID_ZIP", app.extract_zip, zipped.id, "wrong-password", password="wrong-password")


@pytest.mark.parametrize("name", ["../evil", "C:/evil", "\\\\host/share", "file:ads",
                                 "CON.txt", "dir/../../evil", "trail.", "a\\..\\evil"])
def test_zipslip_windows_paths(app, alice, name):
    zipped = app.create("attack.zip", archive([(name, b"owned")]), "zip")
    fails("UNSAFE_NAME", app.extract_zip, zipped.id, "out")
    assert len(app.list_files()) == 1


def test_zip_symlink_and_duplicates(app, alice):
    stream = BytesIO()
    with zipfile.ZipFile(stream, "w") as output:
        info = zipfile.ZipInfo("link")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        output.writestr(info, "../../target")
    info = app.create("link.zip", stream.getvalue(), "zip")
    fails("ZIP_SPECIAL_FILE", app.extract_zip, info.id)
    info = app.create("dup.zip", archive([("a", b"1"), ("A", b"2")]), "zip")
    fails("ZIP_DUPLICATE_NAME", app.extract_zip, info.id)
    info = app.create("conflict.zip", archive([("a", b"1"), ("a/b", b"2")]), "zip")
    fails("ZIP_NAME_CONFLICT", app.extract_zip, info.id)


def test_zip_limits_corruption_and_no_partial_files(app, alice):
    bomb = app.create("bomb.zip", archive([("repeat", b"0" * 100000)]), "zip")
    fails("ZIP_RATIO_LIMIT", app.extract_zip, bomb.id)
    info = app.create("many.zip", archive([("a", b"1"), ("b", b"2")]), "zip")
    app.settings = replace(app.settings, max_zip_files=1)
    fails("ZIP_TOO_MANY_FILES", app.extract_zip, info.id)
    app.settings = replace(app.settings, max_zip_files=1000, max_total_zip_bytes=1)
    fails("ZIP_TOTAL_LIMIT", app.extract_zip, info.id)
    bad = app.create("bad.zip", b"not a zip", "zip")
    fails("INVALID_ZIP", app.extract_zip, bad.id)
    assert len(app.list_files()) == 3


def test_nested_archives_not_recursively_extracted(app, alice):
    info = app.create("outer.zip", archive([("inner.zip", archive([("data", b"x")]))]), "zip")
    files = app.extract_zip(info.id)
    assert len(files) == 1
    assert files[0].format == "binary"
    assert files[0].name.endswith("/inner.zip")


def test_atomic_zip_batch_when_one_document_is_bad(app, alice):
    info = app.create("mixed.zip", archive([("ok.txt", b"good"), ("bad.json", b"invalid")]), "zip")
    fails("INVALID_JSON", app.extract_zip, info.id)
    assert len(app.list_files()) == 1


def test_concurrent_updates_across_instances(app, alice):
    info = app.create("shared", b"initial")
    second = Application(app.settings)
    second.auth.login("alice", PASSWORD)
    try:
        def update(instance, value):
            try:
                instance.update(info.id, value, 1)
                return "ok"
            except FMError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(update, app, b"one"), pool.submit(update, second, b"two")]
            assert sorted(f.result() for f in futures) == ["VERSION_CONFLICT", "ok"]
        assert app.read(info.id) in {b"one", b"two"}
        assert app.journal.verify()
    finally:
        second.close()


def test_concurrent_name_and_quota(app, alice):
    second = Application(app.settings)
    second.auth.login("alice", PASSWORD)
    try:
        def create(instance):
            try:
                instance.create("same", b"data")
                return "ok"
            except FMError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(create, [app, second]))
        assert sorted(results) == ["NAME_CONFLICT", "ok"]
        assert len(app.list_files()) == 1
    finally:
        second.close()


@pytest.mark.parametrize("point", ["after_publish", "after_metadata", "after_audit"])
def test_recovery_after_transaction_abort(app, alice, point):
    original = app.create("stable", b"old")
    app._fault = point
    with pytest.raises(RuntimeError, match="simulated process failure"):
        app.update(original.id, b"new", 1)
    app._fault = None
    assert app.read(original.id) == b"old"
    assert len(list(app.storage.objects.iterdir())) == 2
    app._recover_system()
    assert len(list(app.storage.objects.iterdir())) == 1
    app._recover_system()
    assert app.journal.verify()


def test_failure_audit_survives_main_rollback(app, alice):
    app.create("same", b"one")
    fails("NAME_CONFLICT", app.create, "SAME", b"two")
    with app.db.transaction() as conn:
        assert execute(conn, "SELECT COUNT(*) FROM fm.operations "
                             "WHERE outcome='failure' AND reason='NAME_CONFLICT'").scalar_one() == 1
    assert app.journal.verify()


@pytest.mark.parametrize("mutation", ["payload", "column", "gap", "tail"])
def test_audit_tampering_detected(app, alice, owner_engine, mutation):
    app.create("a", b"data")
    with owner_engine.begin() as conn:
        if mutation == "payload":
            conn.exec_driver_sql("UPDATE fm.operations SET payload=jsonb_set(payload,'{reason}',"
                                 "'\"FORGED\"'::jsonb) WHERE id=1")
        elif mutation == "column":
            conn.exec_driver_sql("UPDATE fm.operations SET action='FORGED' WHERE id=1")
        elif mutation == "gap":
            conn.exec_driver_sql("DELETE FROM fm.operations WHERE id=2")
        else:
            conn.exec_driver_sql("DELETE FROM fm.operations WHERE id=(SELECT max(id) FROM fm.operations)")
            conn.exec_driver_sql("UPDATE fm.audit_head SET seq=(SELECT max(id) FROM fm.operations),"
                                 "signature=(SELECT hmac FROM fm.operations ORDER BY id DESC LIMIT 1)")
    fails("AUDIT_TAMPERED", app.journal.verify)


def test_windows_junction_and_hardlink_rejected(app, alice, tmp_path):
    from pathlib import Path
    locations = app.locations()
    inbox = Path(locations["inbox"])
    target = tmp_path / "outside.txt"
    target.write_bytes(b"secret")
    import win32api
    if win32api.GetVolumeInformation(tmp_path.anchor)[4].upper() != "NTFS":
        pytest.skip("Native NTFS hardlinks/junctions unavailable on this exFAT project volume; "
                    "handle validation is tested independently")
    os.link(target, inbox / "hard.txt")
    fails("HARDLINK_FORBIDDEN", app.import_file, "hard.txt")
    # Native junction creation does not require symlink privilege.
    junction = inbox / "junction"
    # The shell command uses only generated, verified test paths and no deletion.
    completed = subprocess.run(["cmd.exe", "/d", "/c", "mklink", "/J", str(junction), str(tmp_path)],
                               capture_output=True, check=False)  # nosec B603 B607
    if completed.returncode == 0:
        try:
            with pytest.raises(FMError), open_regular(junction / "outside.txt"):
                pass
        finally:
            # Remove only this verified junction, never its target.
            assert junction.parent == inbox and junction.name == "junction"
            junction.rmdir()
    else:
        pytest.fail("Unable to create test junction")


def test_password_change_revokes_other_sessions(app, alice):
    second = Application(app.settings)
    try:
        second.auth.login("alice", PASSWORD)
        fails("PASSWORD_CHANGE_FAILED", app.auth.change_password, "wrong", PASSWORD + "new")
        app.auth.change_password(PASSWORD, PASSWORD + "new")
        fails("LOGIN_REQUIRED", app.list_files)
        fails("SESSION_REVOKED", second.list_files)
        fails("LOGIN_FAILED", app.auth.login, "alice", PASSWORD)
        app.auth.login("alice", PASSWORD + "new")
        assert app.list_files() == []
    finally:
        second.close()


@pytest.mark.parametrize("point", ["after_publish", "after_metadata", "after_audit"])
def test_abrupt_process_death_and_startup_recovery(app, alice, point):
    info = app.create("stable", b"old")
    result = subprocess.run(
        [sys.executable, "tests/crash_client.py", str(app.settings.storage_root), str(info.id), point],
        capture_output=True, timeout=20, check=False,
    )
    assert result.returncode == 97, result.stderr.decode(errors="replace")
    reopened = Application(app.settings)
    try:
        reopened.auth.login("alice", PASSWORD)
        assert reopened.read(info.id) == b"old"
        assert len(list(reopened.storage.objects.iterdir())) == 1
        assert reopened.journal.verify()
    finally:
        reopened.close()


