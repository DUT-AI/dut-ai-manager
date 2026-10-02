"""drop_description_from_homeworks

Revision ID: e1a2b3c4d5f6
Revises: 4790a2b574fc
Create Date: 2026-09-28 09:44:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1a2b3c4d5f6"
down_revision: str | Sequence[str] | None = "4790a2b574fc"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema - drop description column from homeworks table if exists."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c["name"] for c in insp.get_columns("homeworks")]
    if "description" in columns:
        op.drop_column("homeworks", "description")


def downgrade() -> None:
    """Downgrade schema."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    columns = [c["name"] for c in insp.get_columns("homeworks")]
    if "description" not in columns:
        op.add_column("homeworks", sa.Column("description", sa.Text(), nullable=True))
