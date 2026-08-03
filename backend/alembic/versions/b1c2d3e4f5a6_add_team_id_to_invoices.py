"""add team_id to invoices with default logic

Revision ID: b1c2d3e4f5a6
Revises: a9b8c7d6e5f4
Create Date: 2026-08-03 22:15:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b1c2d3e4f5a6"
down_revision = "a9b8c7d6e5f4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("invoices", sa.Column("team_id", sa.Integer(), nullable=True))

    # Fill existing data: default team_id = 6, if amount = 50000 then team_id = 9
    op.execute(
        """
        UPDATE invoices
        SET team_id = CASE
            WHEN amount = 50000 THEN 9
            ELSE 6
        END
        WHERE team_id IS NULL;
        """
    )

    op.alter_column("invoices", "team_id", nullable=False)
    op.create_foreign_key(
        "fk_invoices_team_id_teams",
        "invoices",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(op.f("ix_invoices_team_id"), "invoices", ["team_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_invoices_team_id"), table_name="invoices")
    op.drop_constraint("fk_invoices_team_id_teams", "invoices", type_="foreignkey")
    op.drop_column("invoices", "team_id")
