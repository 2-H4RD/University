"""A test-only process which intentionally dies inside an uncommitted operation."""
import sys
from dataclasses import replace
from pathlib import Path

from filemanager.config import Settings
from filemanager.services.application import Application

if __name__ == "__main__":
    config = Settings.load(".env.test")
    if not config.testing or config.db_name != "secure_filemanager_test":
        raise SystemExit(2)
    app = Application(replace(config, storage_root=Path(sys.argv[1])))
    app.auth.login("alice", "University-test-passphrase-2026!")
    app._fault = "exit:" + sys.argv[3]
    app.update(sys.argv[2], b"uncommitted new content", 1)
    raise SystemExit(3)

