"""merge hw exercises, fund code, and cleaning duty heads

Revision ID: 045_merge_hw_fund_duty_heads
Revises: 044_add_fund_code, 20231116181800, 044_hw_exercises_and_sub_id
Create Date: 2026-11-18 02:20:23.404423

"""
from collections.abc import Sequence

# revision identifiers, used by Alembic.
revision: str = '045_merge_hw_fund_duty_heads'
down_revision: str | Sequence[str] | None = ('044_add_fund_code', '20231116181800', '044_hw_exercises_and_sub_id')
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
