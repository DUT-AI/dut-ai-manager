"""move_homework_deadline_to_assignees

Move deadline column from homeworks table to homework_assignees table.
Backfill existing deadlines from homeworks and active POSTPONE requests,
create index on homework_assignees.deadline, and drop deadline from homeworks.

Revision ID: 039_move_homework_deadline_to_assignees
Revises: 038_fix_participant_timestamptz
Create Date: 2026-10-31 21:30:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "039_move_hw_dl_to_assignees"
down_revision: str | Sequence[str] | None = "038_fix_participant_timestamptz"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add column deadline to homework_assignees if not exists
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = 'homework_assignees' 
                  AND column_name = 'deadline'
            ) THEN
                ALTER TABLE homework_assignees 
                ADD COLUMN deadline timestamp with time zone NULL;
            END IF;
        END $$;
        """
    )

    # 2. Backfill deadline from homeworks
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = 'homeworks' 
                  AND column_name = 'deadline'
            ) THEN
                UPDATE homework_assignees ha
                SET deadline = h.deadline
                FROM homeworks h
                WHERE ha.homework_id = h.id AND ha.deadline IS NULL;
            END IF;
        END $$;
        """
    )

    # 3. Update deadline for active POSTPONE permission requests
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = 'permission_requests' 
                  AND column_name = 'payload'
            ) THEN
                UPDATE homework_assignees ha
                SET deadline = (pr.payload->>'start_time')::timestamptz
                FROM permission_requests pr
                WHERE pr.category = 'POSTPONE'
                  AND (pr.payload->>'homework_id')::int = ha.homework_id
                  AND pr.created_by = ha.user_id
                  AND pr.is_deleted = false
                  AND pr.payload->>'start_time' IS NOT NULL;
            END IF;
        END $$;
        """
    )

    # 4. Set fallback for any remaining NULL deadlines and set NOT NULL
    op.execute(
        """
        UPDATE homework_assignees 
        SET deadline = NOW() AT TIME ZONE 'UTC' 
        WHERE deadline IS NULL;

        ALTER TABLE homework_assignees 
        ALTER COLUMN deadline SET NOT NULL;

        CREATE INDEX IF NOT EXISTS ix_homework_assignees_deadline 
        ON homework_assignees (deadline);
        """
    )

    # 5. Drop column deadline from homeworks
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = 'homeworks' 
                  AND column_name = 'deadline'
            ) THEN
                ALTER TABLE homeworks DROP COLUMN deadline;
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # 1. Re-add deadline to homeworks
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = 'homeworks' 
                  AND column_name = 'deadline'
            ) THEN
                ALTER TABLE homeworks 
                ADD COLUMN deadline timestamp with time zone NULL;
            END IF;
        END $$;
        """
    )

    # 2. Backfill deadline back to homeworks (using min deadline from assignees)
    op.execute(
        """
        UPDATE homeworks h
        SET deadline = sub.min_dl
        FROM (
            SELECT homework_id, MIN(deadline) as min_dl
            FROM homework_assignees
            GROUP BY homework_id
        ) sub
        WHERE h.id = sub.homework_id;
        """
    )

    # 3. Drop index and column deadline from homework_assignees
    op.execute(
        """
        DROP INDEX IF EXISTS ix_homework_assignees_deadline;

        ALTER TABLE homework_assignees 
        DROP COLUMN IF EXISTS deadline;
        """
    )
