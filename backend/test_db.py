from sqlmodel import Session, create_engine, select
from app.core.config import settings
from app.permission_request.infrastructure.model import PermissionRequest

def main():
    engine = create_engine(str(settings.SQLALCHEMY_DATABASE_URI))
    with Session(engine) as session:
        stmt = select(PermissionRequest).where(PermissionRequest.category == "POSTPONE")
        models = session.exec(stmt).all()
        print(f"Total: {len(models)}")
        for m in models:
            e = m.to_entity()
            print(f"ID: {m.id}, creator in model: {m.created_by}, entity created_by: {e.created_by}, entity user_id: {e.user_id}, hw: {e.homework_id}")

main()
