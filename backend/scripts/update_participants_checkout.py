"""
Script to update all meeting_participants where check_out_at is NULL or different from meeting.end_time.
Updates check_out_at to equal meeting.end_time.
"""

import sys
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

# Import all models to register them with SQLAlchemy/SQLModel
from app.auth.infrastructure.model import AccountModel
from app.billing.infrastructure.model import InvoiceItemModel, InvoiceModel
from app.bonus_point.infrastructure.model import BonusPointModel
from app.homework.infrastructure.model import HomeworkModel, HomeworkSubmissionModel
from app.meeting.infrastructure.model import Meeting, MeetingParticipant
from app.permission_request.infrastructure.model import PermissionRequest
from app.rbac.infrastructure.model import (
    PermissionModel,
    RoleApiKeyModel,
    RoleModel,
    RolePermissionModel,
)
from app.team.infrastructure.model import TeamMemberModel, TeamModel
from app.user.infrastructure.model import UserModel
from app.user.infrastructure.monthly_stats_model import MonthlyUserStatsModel
from app.violation.infrastructure.model import ViolationModel

from sqlalchemy import update, select, func
from app.core.database import engine
from sqlalchemy.orm import Session


def main():
    # Check if commit flag is provided in command line arguments
    commit_mode = "--commit" in sys.argv
    
    with Session(engine) as session:
        # Define subquery to fetch the corresponding meeting's end_time
        subquery = (
            select(Meeting.end_time)
            .where(Meeting.id == MeetingParticipant.meeting_id)
            .scalar_subquery()
        )
        
        # Count records that need to be updated
        count_query = (
            select(func.count(MeetingParticipant.id))
            .where(
                (MeetingParticipant.check_out_at.is_(None)) |
                (MeetingParticipant.check_out_at != subquery)
            )
        )
        count_to_update = session.execute(count_query).scalar() or 0
        
        print(f"Found {count_to_update} meeting_participant record(s) needing update.")
        
        if count_to_update == 0:
            print("No records need to be updated.")
            return
            
        if not commit_mode:
            print("[DRY RUN] Run the script with '--commit' to apply changes to the database.")
            return
            
        print("Updating records...")
        update_stmt = (
            update(MeetingParticipant)
            .where(
                (MeetingParticipant.check_out_at.is_(None)) |
                (MeetingParticipant.check_out_at != subquery)
            )
            .values(check_out_at=subquery)
        )
        
        result = session.execute(update_stmt)
        session.commit()
        print(f"Successfully updated {result.rowcount} record(s) in the database.")

if __name__ == "__main__":
    main()
