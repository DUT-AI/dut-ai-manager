import datetime
import random
from loguru import logger
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.user.domain.entity import UserStatus
from app.user.infrastructure.model import UserModel
from app.user.infrastructure.monthly_stats_model import MonthlyUserStatsModel
from app.rbac.infrastructure.model import RoleModel
from app.rbac.domain.entity import RoleType
from app.meeting.infrastructure.model import Meeting, MeetingParticipant
from app.violation.infrastructure.model import ViolationModel
from app.bonus_point.infrastructure.model import BonusPointModel
from app.violation.domain.entity import ViolationType
from app.user.domain.monthly_stats import UserTitle
from app.auth.infrastructure.model import AccountModel
from app.team.infrastructure.model import TeamMemberModel
from app.meeting.domain.entity import ParticipantStatus

def seed_mock_data():
    with Session(engine) as session:
        # Delete old mock data
        session.execute(text("TRUNCATE TABLE monthly_user_stats RESTART IDENTITY CASCADE;"))
        session.execute(text("TRUNCATE TABLE violations RESTART IDENTITY CASCADE;"))
        session.execute(text("TRUNCATE TABLE bonus_points RESTART IDENTITY CASCADE;"))
        session.execute(text("TRUNCATE TABLE meeting_participants RESTART IDENTITY CASCADE;"))
        session.execute(text("TRUNCATE TABLE meetings RESTART IDENTITY CASCADE;"))
        # We don't truncate users so we don't break authentication if any, but let's just delete users created for mock
        session.execute(text("DELETE FROM users WHERE email LIKE 'mock_%'"))
        session.commit()

        # Get teammate role
        role_statement = select(RoleModel).where(RoleModel.name == RoleType.TEAMMATE)
        teammate_role = session.scalars(role_statement).first()
        if not teammate_role:
            logger.error("Teammate role not found.")
            return

        # Create 50 mock users using raw SQL to avoid ENUM casting issues
        for i in range(1, 51):
            session.execute(text("""
                INSERT INTO users (name, email, phone_number, status, role_id, created_at, updated_at, is_deleted)
                VALUES (:name, :email, :phone, 'ACTIVE'::userstatus, :role_id, now(), now(), false)
            """), {
                "name": f"Mock User {i}",
                "email": f"mock_user_{i}@gmail.com",
                "phone": f"0123456{i:03d}",
                "role_id": teammate_role.id
            })
        session.flush()

        # Fetch the created users to use their IDs
        mock_users = session.scalars(select(UserModel).where(UserModel.email.like("mock_user_%"))).all()

        # Date range: 2026-01-01 to 2026-06-16
        start_date = datetime.datetime(2026, 1, 1)
        end_date = datetime.datetime(2026, 6, 16)
        
        meetings = []
        current_date = start_date
        # Create 2 meetings per week
        while current_date <= end_date:
            if current_date.weekday() in [1, 4]: # Tue, Fri
                date_time = datetime.datetime(current_date.year, current_date.month, current_date.day, 18, 0, 0)
                m = Meeting(
                    title=f"Buổi sinh hoạt {current_date.strftime('%d/%m/%Y')}",
                    content="Mock meeting",
                    start_time=date_time,
                    end_time=date_time + datetime.timedelta(hours=2),
                    require_check_in=True,
                )
                meetings.append(m)
            current_date += datetime.timedelta(days=1)
        
        session.add_all(meetings)
        session.flush()

        # Randomize activity for users
        # 10 very active (almost no miss, on time)
        # 20 normal (miss some, late some)
        # 10 poor (miss many, late many)
        # 10 inactive (0 activity)
        
        for idx, user in enumerate(mock_users):
            if idx < 10:
                profile = "ACTIVE"
            elif idx < 30:
                profile = "NORMAL"
            elif idx < 40:
                profile = "POOR"
            else:
                profile = "INACTIVE"
                
            if profile == "INACTIVE":
                continue
                
            for m in meetings:
                if profile == "ACTIVE":
                    if random.random() < 0.95: # 95% attendance
                        # Check in on time
                        cin = m.start_time - datetime.timedelta(minutes=random.randint(0, 10))
                        cout = m.end_time
                        session.execute(text("""
                            INSERT INTO meeting_participants (meeting_id, user_id, check_in_at, check_out_at, status, is_deleted, created_at, updated_at)
                            VALUES (:m_id, :u_id, :cin, :cout, 'JOINED'::participantstatus, false, now(), now())
                        """), {"m_id": m.id, "u_id": user.id, "cin": cin, "cout": cout})
                elif profile == "NORMAL":
                    if random.random() < 0.7: # 70% attendance
                        late = random.random() < 0.2
                        cin = m.start_time + datetime.timedelta(minutes=random.randint(10, 30)) if late else m.start_time - datetime.timedelta(minutes=random.randint(0, 10))
                        cout = m.end_time
                        session.execute(text("""
                            INSERT INTO meeting_participants (meeting_id, user_id, check_in_at, check_out_at, status, is_deleted, created_at, updated_at)
                            VALUES (:m_id, :u_id, :cin, :cout, 'JOINED'::participantstatus, false, now(), now())
                        """), {"m_id": m.id, "u_id": user.id, "cin": cin, "cout": cout})
                        if late:
                            v = ViolationModel(user_id=user.id, date=m.start_time, reason="Đi trễ")
                            session.add(v)
                    else:
                        v = ViolationModel(user_id=user.id, date=m.start_time, reason="Vắng")
                        session.add(v)
                elif profile == "POOR":
                    if random.random() < 0.3: # 30% attendance
                        late = random.random() < 0.5
                        cin = m.start_time + datetime.timedelta(minutes=random.randint(10, 60)) if late else m.start_time - datetime.timedelta(minutes=random.randint(0, 10))
                        cout = m.end_time
                        session.execute(text("""
                            INSERT INTO meeting_participants (meeting_id, user_id, check_in_at, check_out_at, status, is_deleted, created_at, updated_at)
                            VALUES (:m_id, :u_id, :cin, :cout, 'JOINED'::participantstatus, false, now(), now())
                        """), {"m_id": m.id, "u_id": user.id, "cin": cin, "cout": cout})
                        if late:
                            v = ViolationModel(user_id=user.id, date=m.start_time, reason="Đi trễ")
                            session.add(v)
                    else:
                        v = ViolationModel(user_id=user.id, date=m.start_time, reason="Vắng")
                        session.add(v)
        
        session.commit()
        
        # Calculate titles for all months
        from app.report.application.title_use_cases import AssignMonthlyTitlesUseCase
        from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
        from app.bonus_point.infrastructure.repository import BonusPointRepository
        from app.violation.infrastructure.repository import ViolationRepository
        from app.user.infrastructure.repository import UserRepository
        from app.meeting.infrastructure.repository import ParticipantRepository
        from app.report.application.participation_use_cases import GetParticipationAnalysisUseCase
        
        stats_repo = MonthlyUserStatsRepository(session)
        bonus_repo = BonusPointRepository(session)
        violation_repo = ViolationRepository(session)
        user_repo = UserRepository(session)
        participant_repo = ParticipantRepository(session)
        analysis_uc = GetParticipationAnalysisUseCase(participant_repo, violation_repo)
        
        assign_uc = AssignMonthlyTitlesUseCase(stats_repo, bonus_repo, violation_repo, user_repo, analysis_uc)
        
        for m in range(1, 7):
            assign_uc.execute(m, 2026)
            
        session.commit()
        
        logger.success("Mock data (50 users) generated and titles assigned successfully!")

if __name__ == "__main__":
    seed_mock_data()
