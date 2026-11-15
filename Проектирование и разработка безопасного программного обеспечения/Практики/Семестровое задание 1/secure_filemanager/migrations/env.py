import os

from alembic import context
from sqlalchemy import create_engine

from filemanager.config import Settings
from filemanager.errors import FMError
from filemanager.security.secrets import decode_secret

cfg = Settings.load(os.getenv("FM_ENV_FILE", ".env"))
role = os.environ["FM_OWNER_ROLE"]
if role not in {"fm_owner", "fm_test_owner"}:
    raise FMError("INVALID_MIGRATION_ROLE")
url = cfg.url.set(username=os.environ["FM_MIGRATOR_USER"],
                  password=decode_secret(os.environ["FM_MIGRATOR_PASSWORD"]))
engine = create_engine(url, hide_parameters=True)
with engine.connect() as conn:
    # The role is an exact allowlisted identifier, never external free-form input.
    conn.exec_driver_sql("SET ROLE fm_test_owner" if role == "fm_test_owner" else "SET ROLE fm_owner")
    conn.commit()
    context.configure(connection=conn, transaction_per_migration=True)
    with context.begin_transaction():
        context.run_migrations()
engine.dispose()

