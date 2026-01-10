"""update role name to enum

Revision ID: b5eca9e80dcc
Revises: 68039e7ba86e
Create Date: 2026-01-07 15:16:21.492506

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "b5eca9e80dcc"
down_revision: Union[str, Sequence[str], None] = "68039e7ba86e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define the enum
roletype_enum = sa.Enum("ADMIN", "LEADER", "TEAMMATE", name="roletype")


def upgrade() -> None:
    """Upgrade schema."""
    # Create the enum type first
    roletype_enum.create(op.get_bind(), checkfirst=True)

    # Drop the unique index first
    op.drop_index("ix_roles_name", table_name="roles")

    # Alter the column type using raw SQL for PostgreSQL
    op.execute("ALTER TABLE roles ALTER COLUMN name TYPE roletype USING name::roletype")

    # Recreate the unique index
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the unique index first
    op.drop_index("ix_roles_name", table_name="roles")

    # Alter back to VARCHAR
    op.execute("ALTER TABLE roles ALTER COLUMN name TYPE VARCHAR(100) USING name::text")

    # Recreate the unique index
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    # Drop the enum type
    roletype_enum.drop(op.get_bind(), checkfirst=True)
