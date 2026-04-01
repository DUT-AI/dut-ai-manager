"""add check_in_card_code to users

Revision ID: e8f2a1c0b3d4
Revises: 3c38054f3aad
Create Date: 2026-04-01

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel

revision: str = "e8f2a1c0b3d4"
down_revision: Union[str, Sequence[str], None] = "3c38054f3aad"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "check_in_card_code",
            sqlmodel.sql.sqltypes.AutoString(length=64),
            nullable=True,
        ),
    )
    op.create_index(
        op.f("ix_users_check_in_card_code"),
        "users",
        ["check_in_card_code"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_users_check_in_card_code"), table_name="users")
    op.drop_column("users", "check_in_card_code")
