"""add require_check_in to meetings

Revision ID: a1b2c3d4e5f6
Revises: dbe799d143a2
Create Date: 2026-02-17 12:55:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "dbe799d143a2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "meetings",
        sa.Column(
            "require_check_in",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )


def downgrade() -> None:
    op.drop_column("meetings", "require_check_in")
