from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace

import pytest
from conftest import PASSWORD

from filemanager.errors import FMError
from filemanager.repositories.db import execute
from filemanager.security.secrets import decode_secret, encode_secret, seal, unseal
from filemanager.services.application import Application
from filemanager.storage.safeio import open_regular, pin_directory


def test_dpapi_confidentiality_and_tampering():
    secret = b"Never store this database password as plaintext"
    encoded = seal(secret)
    assert secret not in encoded
    assert unseal(encoded) == secret
    assert decode_secret(encode_secret(secret.decode())) == secret.decode()
    changed = encoded[:-1] + bytes([encoded[-1] ^ 1])
    with pytest.raises(FMError):
        unseal(changed)
    with pytest.raises(FMError, match="UNPROTECTED_OR_INVALID_SECRET"):
        unseal(secret)
    with pytest.raises(FMError, match="UNPROTECTED_DATABASE_PASSWORD"):
        decode_secret(secret.decode())


def test_encrypted_objects_and_uuid_binding(app, alice):
    one = app.create("one", b"confidential information")
    two = app.create("two", b"confidential information")
    with app.db.transaction() as conn:
        keys = list(execute(conn, "SELECT storage_key FROM fm.files ORDER BY name").scalars())
    first, second = [app.storage.object_path(key) for key in keys]
    original = first.read_bytes()
    assert original.startswith(b"SFM1")
    assert b"confidential information" not in original
    assert original != second.read_bytes()
    second.write_bytes(original)
    with pytest.raises(FMError, match="FILE_INTEGRITY_FAILED"):
        app.read(two.id)
    assert app.read(one.id) == b"confidential information"
    for path in (app.storage.root / "secrets").glob("*.key"):
        assert path.read_bytes().startswith(b"SFM-DPAPI-1\n")


@pytest.mark.parametrize("attack", ["hardlink", "reparse", "wrong_path"])
def test_opened_handle_validation_even_on_exfat(tmp_path, monkeypatch, attack):
    import win32file
    path = tmp_path / "regular.txt"
    path.write_bytes(b"data")
    real_info = win32file.GetFileInformationByHandle

    def modified_info(handle):
        info = list(real_info(handle))
        if not info[0] & 0x10:
            if attack == "hardlink":
                info[7] = 2
            elif attack == "reparse":
                info[0] |= 0x400
        return tuple(info)

    monkeypatch.setattr(win32file, "GetFileInformationByHandle", modified_info)
    if attack == "wrong_path":
        monkeypatch.setattr(win32file, "GetFinalPathNameByHandle",
                            lambda *_args: "\\\\?\\C:\\outside.txt")
    expected = {"hardlink": "HARDLINK_FORBIDDEN", "reparse": "LINK_FORBIDDEN",
                "wrong_path": "PATH_MISMATCH"}[attack]
    with pytest.raises(FMError, match=expected), open_regular(path):
        pass


def test_pinned_directory_cannot_be_renamed(tmp_path):
    directory = tmp_path / "pinned"
    directory.mkdir()
    with pin_directory(directory), pytest.raises(OSError):
        directory.rename(tmp_path / "moved")
    assert directory.exists()


def test_export_quota_and_file_count(app, alice):
    info = app.create("data", b"1234")
    app.settings = replace(app.settings, user_quota_bytes=8)
    app.export_file(info.id, "first")
    with pytest.raises(FMError, match="USER_QUOTA_EXCEEDED"):
        app.export_file(info.id, "second")
    app.settings = replace(app.settings, user_quota_bytes=100, max_user_files=1)
    with pytest.raises(FMError, match="USER_FILE_COUNT_LIMIT"):
        app.create("extra", b"")
    app.settings = replace(app.settings, max_outbox_files=1)
    with pytest.raises(FMError, match="OUTBOX_FILE_COUNT_LIMIT"):
        app.export_file(info.id, "extra")


def test_concurrent_distinct_names_cannot_exceed_quota(app, alice):
    app.settings = replace(app.settings, user_quota_bytes=10)
    second = Application(app.settings)
    second.auth.login("alice", PASSWORD)
    try:
        def create(args):
            instance, name = args
            try:
                instance.create(name, b"12345678")
                return "ok"
            except FMError as exc:
                return exc.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            result = list(pool.map(create, [(app, "one"), (second, "two")]))
        assert sorted(result) == ["USER_QUOTA_EXCEEDED", "ok"]
        assert len(app.list_files()) == 1
    finally:
        second.close()


def test_audit_failure_rolls_back_metadata(app, alice, monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise FMError("AUDIT_UNAVAILABLE")
    with monkeypatch.context() as patch:
        patch.setattr(app.journal, "append", unavailable)
        with pytest.raises(FMError, match="AUDIT_UNAVAILABLE"):
            app.create("should-not-commit", b"data")
    with app.db.transaction() as conn:
        assert execute(conn, "SELECT COUNT(*) FROM fm.files").scalar_one() == 0
    app._recover_system()
    assert list(app.storage.objects.iterdir()) == []
    assert app.journal.verify()


def test_checkpoint_missing_fails_closed(app, alice):
    app.create("data", b"data")
    app.journal.checkpoint.unlink()
    with pytest.raises(FMError, match="AUDIT_CHECKPOINT_MISSING"):
        app.journal.verify()


def test_hmac_protocols_are_domain_separated(app):
    data = {"seq": 0, "signature": "0" * 64}
    assert app.journal.sign(data) != app.journal.sign(data, b"checkpoint")

