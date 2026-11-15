import io
import sys

import pytest
from conftest import PASSWORD
from dotenv import dotenv_values

from filemanager.config import PROJECT_ROOT, Settings
from filemanager.controllers.cli import dispatch, main, prompt
from filemanager.errors import FMError
from filemanager.security.permissions import protect
from filemanager.security.secrets import encode_secret


def config_file(settings, tmp_path):
    values = dict(dotenv_values(PROJECT_ROOT / ".env.test"))
    values["FM_STORAGE_ROOT"] = str(settings.storage_root)
    path = tmp_path / "cli.env"
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()) + "\n", encoding="utf-8")
    protect(path)
    return str(path)


def test_interactive_cli_registration_and_json(settings, tmp_path, monkeypatch, capsys):
    path = config_file(settings, tmp_path)
    monkeypatch.setattr(sys, "argv", ["secure-fm", "--env", path])
    monkeypatch.setattr(sys, "stdin", io.StringIO(
        'register\nalice\nlogin\nalice\nwhoami\nnew "data.json" json\n{"hello":true}\nlist\nlogout\nexit\n'))
    monkeypatch.setattr("getpass.getpass", lambda _message: PASSWORD)
    assert main() == 0
    output = capsys.readouterr().out
    assert '"registered": "alice"' in output
    assert '"name": "data.json"' in output
    assert PASSWORD not in output


def test_cli_check_and_first_admin(settings, tmp_path, monkeypatch, capsys):
    path = config_file(settings, tmp_path)
    monkeypatch.setattr(sys, "argv", ["secure-fm", "--env", path, "--check"])
    assert main() == 0
    assert '"status": "OK"' in capsys.readouterr().out
    monkeypatch.setattr(sys, "argv", ["secure-fm", "--env", path, "--create-admin"])
    monkeypatch.setattr(sys, "stdin", io.StringIO("admin\n"))
    monkeypatch.setattr("getpass.getpass", lambda _message: PASSWORD)
    assert main() == 0
    assert '"role": "admin"' in capsys.readouterr().out
    monkeypatch.setattr(sys, "stdin", io.StringIO("admin2\n"))
    assert main() == 1
    assert "ADMIN_ALREADY_PROVISIONED" in capsys.readouterr().err


def test_cli_file_commands(app, alice, monkeypatch, capsys):
    info = app.create("a", b"old")
    dispatch(app, ["read", str(info.id)])
    assert "old" in capsys.readouterr().out
    monkeypatch.setattr(sys, "stdin", io.StringIO("new content\n"))
    dispatch(app, ["write", str(info.id), "1"])
    assert app.read(info.id) == b"new content"
    dispatch(app, ["delete", str(info.id), "2"])
    assert app.list_files() == []
    dispatch(app, ["help"])
    dispatch(app, ["whoami"])
    with pytest.raises(FMError):
        dispatch(app, ["unknown"])


def test_console_input_limit_drops_remainder(monkeypatch, capsys):
    monkeypatch.setattr(sys, "stdin", io.StringIO("x" * 100000 + "\nhelp\n"))
    with pytest.raises(FMError, match="INPUT_TOO_LONG"):
        prompt("")
    assert prompt("") == "help"


def test_config_rejects_missing_and_admin_credentials(settings, tmp_path):
    with pytest.raises(FMError, match="CONFIG_MISSING"):
        Settings.load(tmp_path / "absent.env")
    path = tmp_path / "bad.env"
    values = dict(dotenv_values(PROJECT_ROOT / ".env.test"))
    values["FM_DB_USER"] = "postgres"
    values["FM_DB_PASSWORD"] = encode_secret("postgres")
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()), encoding="utf-8")
    with pytest.raises(FMError, match="ADMIN_DB_CREDENTIALS_FORBIDDEN"):
        Settings.load(path)

