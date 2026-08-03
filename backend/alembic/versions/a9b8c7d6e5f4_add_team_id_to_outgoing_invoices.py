"""add team_id to outgoing_invoices

Revision ID: a9b8c7d6e5f4
Revises: f1a2b3c4d5e6
Create Date: 2026-08-03 22:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9b8c7d6e5f4"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "outgoing_invoices", sa.Column("team_id", sa.Integer(), nullable=True)
    )

    # Set default team for existing records if any exist
    op.execute(
        """
        UPDATE outgoing_invoices
        SET team_id = (SELECT id FROM teams ORDER BY id ASC LIMIT 1)
        WHERE team_id IS NULL;
        """
    )

    op.alter_column("outgoing_invoices", "team_id", nullable=False)
    op.create_foreign_key(
        "fk_outgoing_invoices_team_id_teams",
        "outgoing_invoices",
        "teams",
        ["team_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        op.f("ix_outgoing_invoices_team_id"),
        "outgoing_invoices",
        ["team_id"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_outgoing_invoices_team_id"), table_name="outgoing_invoices")
    op.drop_constraint(
        "fk_outgoing_invoices_team_id_teams", "outgoing_invoices", type_="foreignkey"
    )
    op.drop_column("outgoing_invoices", "team_id")
