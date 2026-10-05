"""set_requires_coding_true_for_all_homeworks

Revision ID: e7f2b1a9c8d3
Revises: f3e2d1c0b9a8
Create Date: 2026-10-05 17:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "e7f2b1a9c8d3"
down_revision: str | Sequence[str] | None = "f3e2d1c0b9a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Set requires_coding to true for all existing homework rows and update column default."""
    op.execute("UPDATE homeworks SET requires_coding = true;")
    op.alter_column("homeworks", "requires_coding", server_default=sa.text("true"))


def downgrade() -> None:
    """Revert server default back to false."""
    op.alter_column("homeworks", "requires_coding", server_default=sa.text("false"))
