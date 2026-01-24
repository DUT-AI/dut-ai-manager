"""change role name to string

Revision ID: 4604c5a5dee4
Revises: 1533e4e0432b
Create Date: 2026-01-20 14:36:09.458097

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "4604c5a5dee4"
down_revision: Union[str, Sequence[str], None] = "1533e4e0432b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Drop the unique index first
    op.drop_index("ix_roles_name", table_name="roles")

    # Alter the column type to VARCHAR
    op.execute("ALTER TABLE roles ALTER COLUMN name TYPE VARCHAR(100) USING name::text")

    # Recreate the unique index
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique index first
    op.drop_index("ix_roles_name", table_name="roles")

    # Alter back to Enum
    op.execute("ALTER TABLE roles ALTER COLUMN name TYPE roletype USING name::roletype")

    # Recreate the unique index
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)
