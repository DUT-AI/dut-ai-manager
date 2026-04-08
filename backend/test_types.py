import asyncio
from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.permission_request.infrastructure.model import PermissionRequest

def main():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as session:
        stmt = select(PermissionRequest).where(PermissionRequest.id.in_([127, 128, 130]))
        models = session.exec(stmt).all()
        
        for m in models:
            r = m.to_entity()
            key = (r.created_by, r.homework_id)
            print(f"Request ID: {r.id}, Created_by: {r.created_by}, HW_ID: {r.homework_id}, Tuple: {key}, Type1: {type(r.created_by)}, Type2: {type(r.homework_id)}")

main()
