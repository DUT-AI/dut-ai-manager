"""add billing_period to invoices

Revision ID: 226397f44e99
Revises: a7b8c9d0e1f2
Create Date: 2026-06-19 21:26:11.061466

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "226397f44e99"
down_revision: Union[str, Sequence[str], None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Add column as nullable first to support existing data
    op.add_column("invoices", sa.Column("billing_period", sa.Date(), nullable=True))

    # 2. Update existing records according to user rules
    op.execute(
        """
        UPDATE invoices
        SET billing_period = CASE
            WHEN EXTRACT(YEAR FROM created_at) = 2026 AND EXTRACT(MONTH FROM created_at) = 6 AND EXTRACT(DAY FROM created_at) = 11 THEN '2026-05-01'::date
            WHEN EXTRACT(YEAR FROM created_at) = 2026 AND EXTRACT(MONTH FROM created_at) = 5 AND EXTRACT(DAY FROM created_at) = 31 THEN '2026-04-01'::date
            WHEN EXTRACT(YEAR FROM created_at) = 2026 AND EXTRACT(MONTH FROM created_at) = 5 AND EXTRACT(DAY FROM created_at) = 23 THEN '2026-03-01'::date
            ELSE '2026-03-01'::date
        END;
        """
    )

    # 3. Alter column to be NOT NULL now that all records have values
    op.alter_column("invoices", "billing_period", nullable=False)

    # 4. Create index
    op.create_index(
        op.f("ix_invoices_billing_period"), "invoices", ["billing_period"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_invoices_billing_period"), table_name="invoices")
    op.drop_column("invoices", "billing_period")
