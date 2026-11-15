from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection

from filemanager.config import Settings


class Database:
    def __init__(self, settings: Settings):
        self.engine = create_engine(
            settings.url, pool_pre_ping=True, pool_size=4, max_overflow=2,
            connect_args={"connect_timeout": 5,
                          "options": "-c search_path=fm,pg_catalog -c statement_timeout=10000 "
                                     "-c lock_timeout=5000 -c idle_in_transaction_session_timeout=15000"},
            hide_parameters=True,
        )

    def transaction(self):
        return self.engine.begin()

    def close(self):
        self.engine.dispose()


def execute(conn: Connection, query: str, **params):
    return conn.execute(text(query), params)


def storage_lock(conn: Connection):
    # One writer across threads/processes; protects quotas, jobs and recovery too.
    execute(conn, "SELECT pg_advisory_xact_lock(73490101)")

