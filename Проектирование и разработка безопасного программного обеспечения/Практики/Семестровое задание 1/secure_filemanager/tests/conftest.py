import os
from dataclasses import replace
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text

from filemanager.config import Settings
from filemanager.security.secrets import decode_secret
from filemanager.services.application import Application

PASSWORD = "University-test-passphrase-2026!"


def pytest_configure(config):
    root = Path(__file__).resolve().parents[1] / "test-var"
    root.mkdir(exist_ok=True)
    selected = Path(config.option.basetemp or root / "pytest").absolute()
    if not selected.is_relative_to(root) or selected == root:
        raise pytest.UsageError("basetemp must be a subdirectory of the project's test-var")
    config.option.basetemp = str(selected)


@pytest.fixture
def settings(tmp_path):
    config = Settings.load(".env.test")
    if not config.testing or config.db_name != "secure_filemanager_test":
        pytest.fail("Refusing to reset anything except the dedicated test database")
    owner = os.environ["FM_OWNER_ROLE"]
    if owner != "fm_test_owner":
        pytest.fail("Wrong test owner")
    engine = create_engine(config.url.set(username=os.environ["FM_MIGRATOR_USER"],
                                         password=decode_secret(os.environ["FM_MIGRATOR_PASSWORD"])))
    with engine.begin() as conn:
        assert conn.execute(text("SELECT current_database()")).scalar_one() == "secure_filemanager_test"
        conn.exec_driver_sql("SET ROLE fm_test_owner")
        conn.exec_driver_sql("TRUNCATE fm.operations,fm.audit_head,fm.files,fm.users,"
                             "fm.auth_attempts,fm.storage_jobs")
        conn.exec_driver_sql("INSERT INTO fm.audit_head VALUES (TRUE,0,repeat('0',64))")
    engine.dispose()
    return replace(config, storage_root=tmp_path / "store")


@pytest.fixture
def app(settings):
    instance = Application(settings)
    yield instance
    instance.close()


@pytest.fixture
def alice(app):
    actor = app.auth.register("alice", PASSWORD)
    app.auth.login("alice", PASSWORD)
    return actor


@pytest.fixture
def owner_engine(settings):
    engine = create_engine(settings.url.set(username=os.environ["FM_MIGRATOR_USER"],
                                           password=decode_secret(os.environ["FM_MIGRATOR_PASSWORD"])))
    with engine.connect() as conn:
        conn.exec_driver_sql("SET ROLE fm_test_owner")
        conn.commit()
    # Install SET ROLE for all connections, not just whichever pool slot was used.
    from sqlalchemy import event

    @event.listens_for(engine, "checkout")
    def set_role(dbapi_connection, *_args):
        with dbapi_connection.cursor() as cursor:
            cursor.execute("SET ROLE fm_test_owner")
        dbapi_connection.commit()
    yield engine
    engine.dispose()

