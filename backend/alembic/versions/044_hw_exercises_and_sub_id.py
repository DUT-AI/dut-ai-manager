"""add homework_exercises catalog, last_synced_at, and external_submission_id

Revision ID: 044_hw_exercises_and_sub_id
Revises: b0a90fa04270
Create Date: 2026-11-18 01:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "044_hw_exercises_and_sub_id"
down_revision: str | Sequence[str] | None = "b0a90fa04270"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create official homework_exercises table and add sync/idempotency columns."""
    # 1. Create homework_exercises table (Official required coding exercises catalog)
    op.create_table(
        "homework_exercises",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("homework_id", sa.Integer(), nullable=False),
        sa.Column("exercise_id", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("order_index", sa.Integer(), server_default="0", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["homework_id"], ["homeworks.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "homework_id", "exercise_id", name="uq_hw_exercises_hw_ex"
        ),
    )
    op.create_index(
        "ix_hw_exercises_hw_active",
        "homework_exercises",
        ["homework_id", "is_active"],
        unique=False,
    )

    # 2. Add last_synced_at column to homeworks
    op.add_column(
        "homeworks",
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 3. Add external_submission_id column to homework_submissions
    op.add_column(
        "homework_submissions",
        sa.Column("external_submission_id", sa.String(length=128), nullable=True),
    )

    # 4. Backfill external_submission_id from details JSON & deduplicate on PostgreSQL
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute(
            sa.text(
                """
                UPDATE homework_submissions
                SET external_submission_id = COALESCE(
                    NULLIF(TRIM(details::jsonb ->> 'submission_id'), ''),
                    NULLIF(TRIM(details::jsonb ->> 'session_id'), '')
                )
                WHERE external_submission_id IS NULL
                  AND details IS NOT NULL
                  AND COALESCE(
                      NULLIF(TRIM(details::jsonb ->> 'submission_id'), ''),
                      NULLIF(TRIM(details::jsonb ->> 'session_id'), '')
                  ) IS NOT NULL
                """
            )
        )
        op.execute(
            sa.text(
                """
                DELETE FROM homework_submissions a
                USING (
                    SELECT id,
                           ROW_NUMBER() OVER (
                               PARTITION BY homework_id, user_id, submission_type, external_submission_id
                               ORDER BY is_passed DESC, submitted_at ASC, id ASC
                           ) AS rn
                    FROM homework_submissions
                    WHERE external_submission_id IS NOT NULL
                ) b
                WHERE a.id = b.id AND b.rn > 1
                """
            )
        )

    # 5. Create partial unique index on external_submission_id
    op.create_index(
        "uq_hw_sub_external_id",
        "homework_submissions",
        ["homework_id", "user_id", "submission_type", "external_submission_id"],
        unique=True,
        postgresql_where=sa.text("external_submission_id IS NOT NULL"),
    )


def downgrade() -> None:
    """Revert homework_exercises table, last_synced_at, and external_submission_id."""
    op.drop_index("uq_hw_sub_external_id", table_name="homework_submissions")
    op.drop_column("homework_submissions", "external_submission_id")
    op.drop_column("homeworks", "last_synced_at")
    op.drop_index("ix_hw_exercises_hw_active", table_name="homework_exercises")
    op.drop_table("homework_exercises")
