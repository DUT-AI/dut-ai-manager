# -*- coding: utf-8 -*-
"""Add responsible_ids and random_round to cleaning_duties and backfill existing duties

Revision ID: 20231116181800
Revises: b0a90fa04270
Create Date: 2023-11-16 18:18:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20231116181800'
down_revision = 'b0a90fa04270'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add columns with safe defaults
    op.execute(
        "ALTER TABLE cleaning_duties ADD COLUMN IF NOT EXISTS responsible_ids JSONB NOT NULL DEFAULT '[]';"
    )
    op.execute(
        "ALTER TABLE cleaning_duties ADD COLUMN IF NOT EXISTS random_round INTEGER NOT NULL DEFAULT 1;"
    )

    # 2. Backfill existing rows if responsible_ids is NULL
    op.execute(
        "UPDATE cleaning_duties SET responsible_ids = '[]' WHERE responsible_ids IS NULL;"
    )
    op.execute(
        "UPDATE cleaning_duties SET random_round = 1 WHERE random_round IS NULL;"
    )

    # 3. Đồng bộ dữ liệu cũ: Nếu checklist đã có assignee_id thì backfill vào responsible_ids
    op.execute("""
        UPDATE cleaning_duties
        SET responsible_ids = (
            SELECT COALESCE(jsonb_agg(DISTINCT (item->>'assignee_id')::int), '[]'::jsonb)
            FROM jsonb_array_elements(checklist) AS item
            WHERE (item->>'assignee_id') IS NOT NULL AND (item->>'assignee_id') ~ '^[0-9]+$'
        )
        WHERE (responsible_ids = '[]'::jsonb OR responsible_ids IS NULL)
          AND jsonb_typeof(checklist) = 'array';
    """)

    # 4. Remove server defaults
    op.alter_column('cleaning_duties', 'responsible_ids', server_default=None)
    op.alter_column('cleaning_duties', 'random_round', server_default=None)


def downgrade():
    op.drop_column('cleaning_duties', 'random_round')
    op.drop_column('cleaning_duties', 'responsible_ids')
