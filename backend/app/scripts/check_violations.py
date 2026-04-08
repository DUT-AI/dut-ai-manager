import asyncio
from sqlmodel import select
from app.core.database import get_db
from app.violation.infrastructure.model import ViolationModel

async def main():
    async for session in get_db():
        stmt = select(ViolationModel).where(ViolationModel.user_id.in_([13, 15, 12]))
        violations = session.exec(stmt).all()
        for v in violations:
            print(f"Violation - User: {v.user_id}, Date: {v.date}, Reason: {v.reason}, Created_at: {v.created_at}")
        return

if __name__ == "__main__":
    asyncio.run(main())
