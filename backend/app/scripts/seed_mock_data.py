import datetime
from loguru import logger
from sqlalchemy import select
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

def seed_mock_data():
    with Session(engine) as session:
        # Get teammate role
        role_statement = select(RoleModel).where(RoleModel.name == RoleType.TEAMMATE)
        teammate_role = session.scalars(role_statement).first()
        if not teammate_role:
            logger.error("Teammate role not found. Run seed_permissions first.")
            return

        # Users
        mock_users = [
            {"name": "Nguyễn Văn A", "email": "nguyenvana@gmail.com", "phone_number": "0123456789"},
            {"name": "Trần Thị B", "email": "tranthib@gmail.com", "phone_number": "0987654321"},
            {"name": "Lê Văn C (Inactive)", "email": "levanc@gmail.com", "phone_number": "0112233445"}, # This user will have no activity
        ]

        created_users = []
        for u_data in mock_users:
            stmt = select(UserModel).where(UserModel.email == u_data["email"])
            existing = session.scalars(stmt).first()
            if not existing:
                user = UserModel(
                    name=u_data["name"],
                    email=u_data["email"],
                    phone_number=u_data["phone_number"],
                    status=UserStatus.ACTIVE,
                    role_id=teammate_role.id
                )
                session.add(user)
                session.flush()
                created_users.append(user)
            else:
                created_users.append(existing)

        session.commit()
        
        user_a = created_users[0]
        user_b = created_users[1]
        user_c = created_users[2]

        now = datetime.datetime.now()
        current_month = now.month
        current_year = now.year

        last_month = current_month - 1
        last_month_year = current_year
        if last_month == 0:
            last_month = 12
            last_month_year -= 1

        # Helper to create meeting
        def create_meeting(month, year, day, name):
            date = datetime.datetime(year, month, day, 18, 0, 0)
            meeting = Meeting(
                title=name,
                content="Mock meeting",
                start_time=date,
                end_time=date + datetime.timedelta(hours=2),
                require_check_in=True,
            )
            session.add(meeting)
            session.flush()
            return meeting

        # Check existing meetings
        if True:
            # Meetings for last month
            m_may_1 = create_meeting(last_month, last_month_year, 10, "Buổi sinh hoạt tháng " + str(last_month) + " - 1")
            m_may_2 = create_meeting(last_month, last_month_year, 20, "Buổi sinh hoạt tháng " + str(last_month) + " - 2")

            # Meetings for current month
            m_june_1 = create_meeting(current_month, current_year, 5, "Buổi sinh hoạt tháng " + str(current_month) + " - 1")

            # Participants (A and B, C has none)
            def add_participant(user_id, meeting, checkin_offset=0):
                from sqlalchemy import text
                checkin = meeting.start_time + datetime.timedelta(minutes=checkin_offset)
                checkout = meeting.end_time
                session.execute(text("""
                    INSERT INTO meeting_participants (meeting_id, user_id, check_in_at, check_out_at, status, is_deleted, created_at, updated_at)
                    VALUES (:m_id, :u_id, :cin, :cout, 'JOINED', false, now(), now())
                """), {"m_id": meeting.id, "u_id": user_id, "cin": checkin, "cout": checkout})

            add_participant(user_a.id, m_may_1, checkin_offset=0) # on time
            add_participant(user_b.id, m_may_1, checkin_offset=20) # late

            add_participant(user_a.id, m_may_2, checkin_offset=0)
            add_participant(user_b.id, m_may_2, checkin_offset=0)

            add_participant(user_a.id, m_june_1, checkin_offset=0)
            
            # Bonus points & violations
            v1 = ViolationModel(user_id=user_b.id, date=m_may_1.start_time, reason="Đi trễ")
            b1 = BonusPointModel(user_id=user_a.id, points=10, reason="Phát biểu tích cực", date=m_may_1.start_time)
            b2 = BonusPointModel(user_id=user_b.id, points=5, reason="Làm bài tập tốt", date=m_may_2.start_time)
            b3 = BonusPointModel(user_id=user_a.id, points=15, reason="Hỗ trợ tech", date=m_june_1.start_time)

            session.add_all([v1, b1, b2, b3])

            # Monthly stats
            stat_a_may = MonthlyUserStatsModel(user_id=user_a.id, month=last_month, year=last_month_year, total_activity_hours=4.0, total_bonus_points=10, violation_count=0, assigned_title=UserTitle.ACTIVE.value)
            stat_b_may = MonthlyUserStatsModel(user_id=user_b.id, month=last_month, year=last_month_year, total_activity_hours=3.6, total_bonus_points=5, late_count=1, violation_count=1, assigned_title=UserTitle.NORMAL.value)
            
            stat_a_june = MonthlyUserStatsModel(user_id=user_a.id, month=current_month, year=current_year, total_activity_hours=2.0, total_bonus_points=15, violation_count=0)
            stat_b_june = MonthlyUserStatsModel(user_id=user_b.id, month=current_month, year=current_year, total_activity_hours=0.0, total_bonus_points=0, violation_count=0)

            # C never has stats or zero stats
            stat_c_may = MonthlyUserStatsModel(user_id=user_c.id, month=last_month, year=last_month_year, total_activity_hours=0.0, total_bonus_points=0, violation_count=0)
            stat_c_june = MonthlyUserStatsModel(user_id=user_c.id, month=current_month, year=current_year, total_activity_hours=0.0, total_bonus_points=0, violation_count=0)

            session.add_all([stat_a_may, stat_b_may, stat_a_june, stat_b_june, stat_c_may, stat_c_june])

            session.commit()
            logger.success("Mock data seeded successfully.")
        else:
            logger.info("Mock data already exists.")

if __name__ == "__main__":
    seed_mock_data()
