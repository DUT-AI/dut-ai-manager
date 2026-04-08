import asyncio
from sqlmodel import Session, create_engine
from app.core.config import settings
from app.homework.infrastructure.repository import HomeworkSubmissionRepository
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.homework.application.use_cases import CheckOverdueHomeworkUseCase
from datetime import datetime

class MockEventBus:
    def __init__(self):
        self.events = []
    @classmethod
    async def publish(cls, event):
        print(f"PUBLISHING VIOLATION: User {event.user_id}, HW: {event.homework_id}, Reason: {event.reason}")

async def main():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as session:
        sub_repo = HomeworkSubmissionRepository(session)
        perm_repo = PermissionRequestRepository(session)
        
        use_case = CheckOverdueHomeworkUseCase(sub_repo, perm_repo)
        
        # Monkey patch the event bus publish in CheckOverdueHomeworkUseCase
        import app.homework.application.use_cases
        app.homework.application.use_cases.EventBus.publish = MockEventBus.publish
        
        target_date = datetime.strptime("2026-04-07", "%Y-%m-%d").date()
        created = await use_case.execute(target_date)
        print(f"Created {created} violations.")

asyncio.run(main())
