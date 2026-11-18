"""add fund_code to invoices and outgoing_invoices

Revision ID: 044_add_fund_code
Revises: b0a90fa04270
Create Date: 2026-11-16 21:20:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '044_add_fund_code'
down_revision: Union[str, Sequence[str], None] = 'b0a90fa04270'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add fund_code as nullable to invoices
    op.add_column('invoices', sa.Column('fund_code', sa.String(length=50), nullable=True))

    # 2. Add fund_code as nullable to outgoing_invoices
    op.add_column('outgoing_invoices', sa.Column('fund_code', sa.String(length=50), nullable=True))

    # 3. Dynamic Backfill existing records:
    # Match by team_name in `teams` table (independent of environment IDs)
    op.execute(
        """
        UPDATE invoices
        SET fund_code = 'DUT_MAKER'
        WHERE team_id IN (
            SELECT id FROM teams WHERE team_name ILIKE '%DUT%Maker%'
        );
        """
    )
    op.execute(
        """
        UPDATE invoices
        SET fund_code = 'DUT_AI'
        WHERE fund_code IS NULL;
        """
    )

    op.execute(
        """
        UPDATE outgoing_invoices
        SET fund_code = 'DUT_MAKER'
        WHERE team_id IN (
            SELECT id FROM teams WHERE team_name ILIKE '%DUT%Maker%'
        );
        """
    )
    op.execute(
        """
        UPDATE outgoing_invoices
        SET fund_code = 'DUT_AI'
        WHERE fund_code IS NULL;
        """
    )

    # 4. Clean up team_id for records where team was solely used to represent fund
    op.execute(
        """
        UPDATE invoices
        SET team_id = NULL
        WHERE team_id IN (
            SELECT id FROM teams WHERE team_name ILIKE '%DUT%Maker%' OR team_name ILIKE '%DUT%AI%'
        );
        """
    )
    op.execute(
        """
        UPDATE outgoing_invoices
        SET team_id = NULL
        WHERE team_id IN (
            SELECT id FROM teams WHERE team_name ILIKE '%DUT%Maker%' OR team_name ILIKE '%DUT%AI%'
        );
        """
    )

    # 5. Set fund_code to NOT NULL with default 'DUT_AI'
    op.alter_column('invoices', 'fund_code', nullable=False, server_default='DUT_AI')
    op.alter_column('outgoing_invoices', 'fund_code', nullable=False, server_default='DUT_AI')

    # 6. Create index on fund_code
    op.create_index(op.f('ix_invoices_fund_code'), 'invoices', ['fund_code'], unique=False)
    op.create_index(op.f('ix_outgoing_invoices_fund_code'), 'outgoing_invoices', ['fund_code'], unique=False)

    # 7. Make team_id nullable so invoices/expenses are not strictly required to link to a team
    op.alter_column('invoices', 'team_id', nullable=True)
    op.alter_column('outgoing_invoices', 'team_id', nullable=True)


def downgrade() -> None:
    # 1. Revert team_id to NOT NULL (safely link to first available team if NULL, without hardcoded ID)
    op.execute(
        """
        UPDATE invoices
        SET team_id = (SELECT id FROM teams ORDER BY id ASC LIMIT 1)
        WHERE team_id IS NULL;
        """
    )
    op.execute(
        """
        UPDATE outgoing_invoices
        SET team_id = (SELECT id FROM teams ORDER BY id ASC LIMIT 1)
        WHERE team_id IS NULL;
        """
    )
    op.alter_column('invoices', 'team_id', nullable=False)
    op.alter_column('outgoing_invoices', 'team_id', nullable=False)

    # 2. Drop indexes
    op.drop_index(op.f('ix_outgoing_invoices_fund_code'), table_name='outgoing_invoices')
    op.drop_index(op.f('ix_invoices_fund_code'), table_name='invoices')

    # 3. Drop columns
    op.drop_column('outgoing_invoices', 'fund_code')
    op.drop_column('invoices', 'fund_code')
