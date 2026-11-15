"""Session revocation and bounded login-attempt retention."""
from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE fm.users ADD COLUMN IF NOT EXISTS auth_version "
               "INTEGER NOT NULL DEFAULT 1 CHECK (auth_version > 0)")
    owner = op.get_bind().exec_driver_sql("SELECT current_user").scalar_one()
    op.execute("GRANT DELETE ON fm.auth_attempts TO fm_test_app" if owner == "fm_test_owner"
               else "GRANT DELETE ON fm.auth_attempts TO fm_app")


def downgrade():
    raise RuntimeError("Destructive downgrade is disabled")

