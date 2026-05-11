import sys
import os

# Thêm thư mục backend vào sys.path để import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.shared.infrastructure.database import get_session, create_db_and_tables
from app.user.infrastructure.monthly_stats_model import MonthlyUserStatsModel
from app.user.infrastructure.model import UserModel
from app.user.domain.monthly_stats import UserTitle
from sqlalchemy import delete
import app.main # Import to load all models

def seed_monthly_stats():
    # Tạo bảng nếu chưa có
    create_db_and_tables()
    
    # get_session returns a generator, so we use next() to get the session
    session_generator = get_session()
    session = next(session_generator)
    
    try:
        # Xóa dữ liệu cũ của tháng 5/2026
        session.execute(
            delete(MonthlyUserStatsModel).where(
                MonthlyUserStatsModel.month == 5, MonthlyUserStatsModel.year == 2026
            )
        )
        
        # Danh sách mock data
        mock_stats = [
            MonthlyUserStatsModel(
                user_id=1, month=5, year=2026,
                total_activity_hours=20.5, total_bonus_points=45,
                late_count=0, absent_count=0, violation_count=0,
                assigned_title=UserTitle.ACTIVE.value
            ),
            MonthlyUserStatsModel(
                user_id=2, month=5, year=2026,
                total_activity_hours=15.0, total_bonus_points=10,
                late_count=1, absent_count=0, violation_count=1,
                assigned_title=UserTitle.NORMAL.value
            ),
            MonthlyUserStatsModel(
                user_id=3, month=5, year=2026,
                total_activity_hours=5.0, total_bonus_points=0,
                late_count=2, absent_count=1, violation_count=3,
                assigned_title=UserTitle.POOR.value
            ),
            MonthlyUserStatsModel(
                user_id=4, month=5, year=2026,
                total_activity_hours=30.0, total_bonus_points=120,
                late_count=0, absent_count=0, violation_count=0,
                assigned_title=UserTitle.ACTIVE.value
            ),
        ]
        
        session.add_all(mock_stats)
        
        # trigger commit and cleanup
        try:
            next(session_generator)
        except StopIteration:
            pass
            
        print("Đã tạo dữ liệu giả cho bảng danh hiệu (tháng 5/2026) thành công!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    seed_monthly_stats()
