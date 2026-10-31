"""add_participant_role

Revision ID: 040_add_participant_role
Revises: 039_move_hw_dl_to_assignees
Create Date: 2026-11-01 01:55:00.000000

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "040_add_participant_role"
down_revision: str | Sequence[str] | None = "039_move_hw_dl_to_assignees"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Add column role to meeting_participants if not exists
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'public' 
                  AND table_name = 'meeting_participants' 
                  AND column_name = 'role'
            ) THEN
                ALTER TABLE meeting_participants 
                ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE';
            END IF;
        END $$;
        """
    )

    # 2. Create indexes for role
    op.execute(
        """
        CREATE INDEX IF NOT EXISTS ix_meeting_participants_role 
        ON meeting_participants (role);
        
        CREATE INDEX IF NOT EXISTS ix_meeting_participants_meeting_role 
        ON meeting_participants (meeting_id, role);
        """
    )

    # 3. Data Migration / Backfill (Zero fallback - 100% normalized):
    # 3a. Update existing participant record of created_by to TRAINER and un-delete if soft-deleted
    op.execute(
        """
        UPDATE meeting_participants mp
        SET role = 'TRAINER', is_deleted = false
        FROM meetings m
        WHERE mp.meeting_id = m.id AND mp.user_id = m.created_by;
        """
    )

    # 3b. Insert a TRAINER participant record for meetings where created_by is not yet an active trainer
    op.execute(
        """
        INSERT INTO meeting_participants (
            meeting_id, user_id, role, status, check_in_at, created_at, updated_at, is_deleted
        )
        SELECT 
            m.id, 
            m.created_by, 
            'TRAINER', 
            'JOINED', 
            m.start_time, 
            COALESCE(m.created_at, NOW()), 
            COALESCE(m.created_at, NOW()),
            false
        FROM meetings m
        WHERE m.created_by IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM meeting_participants mp 
              WHERE mp.meeting_id = m.id AND mp.role = 'TRAINER' AND mp.is_deleted = false
          );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DROP INDEX IF EXISTS ix_meeting_participants_meeting_role;
        DROP INDEX IF EXISTS ix_meeting_participants_role;
        ALTER TABLE meeting_participants DROP COLUMN IF EXISTS role;
        """
    )
