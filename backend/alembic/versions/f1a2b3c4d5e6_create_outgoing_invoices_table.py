"""create outgoing_invoices table

Revision ID: f1a2b3c4d5e6
Revises: 226397f44e99
Create Date: 2026-08-03 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f1a2b3c4d5e6"
down_revision = "fb41d35d7be2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "outgoing_invoices",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("expense_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("spender_id", sa.Integer(), nullable=False),
        sa.Column(
            "status", sa.String(length=50), nullable=False, server_default="UNPAID"
        ),
        sa.Column("payment_date", sa.Date(), nullable=True),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column("updated_by", sa.Integer(), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["spender_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_outgoing_invoices_expense_date"),
        "outgoing_invoices",
        ["expense_date"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outgoing_invoices_spender_id"),
        "outgoing_invoices",
        ["spender_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_outgoing_invoices_status"),
        "outgoing_invoices",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_outgoing_invoices_status"), table_name="outgoing_invoices")
    op.drop_index(
        op.f("ix_outgoing_invoices_spender_id"), table_name="outgoing_invoices"
    )
    op.drop_index(
        op.f("ix_outgoing_invoices_expense_date"), table_name="outgoing_invoices"
    )
    op.drop_table("outgoing_invoices")
