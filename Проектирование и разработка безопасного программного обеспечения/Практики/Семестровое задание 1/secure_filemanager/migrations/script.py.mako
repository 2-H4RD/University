"""Migration."""
from alembic import op
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = None
depends_on = None
def upgrade():
    pass
def downgrade():
    raise RuntimeError("Destructive downgrade is disabled")

