import asyncio
from app.core.database import get_db
from app.permission_request.infrastructure.model import PermissionRequest
from sqlmodel import select
from loguru import logger

async def main():
    async for session in get_db():
        stmt = select(PermissionRequest).where(PermissionRequest.id.in_([127, 128, 130]))
        rows = session.exec(stmt).all()
        for r in rows:
            print(f"Row {r.id}: hw={r.homework_id}, category={r.category}, created_by={r.created_by}")
            e = r.to_entity()
            print(f"Entity: hw={e.homework_id}, created_by={e.created_by}, user_id={e.user_id}")
        return

if __name__ == "__main__":
    asyncio.run(main())
