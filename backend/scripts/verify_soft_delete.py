import sys
import os
from datetime import datetime

# Ensure we can import app
sys.path.append(os.getcwd())

from sqlmodel import Session, select, desc
from app.core.database import engine
from app.models.homework import Homework
from app.api.v1.repositories.homework_repository import HomeworkRepository


def verify():
    print("Starting Soft Delete Verification")
    with Session(engine) as session:
        repo = HomeworkRepository(session)

        # 1. Create a homework
        hw = Homework(
            title="Soft Delete Verification Task",
            deadline=datetime.now(),
            description="Testing soft delete",
        )
        created_hw = repo.create(hw)
        hw_id = created_hw.id
        print(f"[PASS] Created homework with ID: {hw_id}")

        # 2. Verify existence
        fetched = repo.get_by_id(hw_id)
        assert fetched is not None, "Failed to fetch created homework"
        print("[PASS] Fetched homework by ID")

        all_hw = repo.get_all()
        assert any(h.id == hw_id for h in all_hw), "Failed to find homework in get_all"
        print("[PASS] Found homework in get_all")

        # 3. Soft Delete
        repo.delete(fetched)
        print("[PASS] Called delete on homework")

        # 4. Verify filtered out
        session.expire_all()  # Ensure we fetch fresh data
        fetched_after = repo.get_by_id(hw_id)
        assert (
            fetched_after is None
        ), "Homework still returned by get_by_id after delete"
        print("[PASS] get_by_id returns None after delete")

        all_hw_after = repo.get_all()
        assert not any(
            h.id == hw_id for h in all_hw_after
        ), "Homework still returned by get_all after delete"
        print("[PASS] get_all excludes deleted homework")

        # 5. Verify physical existence and is_deleted=True
        statement = select(Homework).where(Homework.id == hw_id)
        raw_hw = session.exec(statement).first()
        assert raw_hw is not None, "Homework row physically deleted from DB!"
        assert (
            raw_hw.is_deleted is True
        ), f"Homework is_deleted is {raw_hw.is_deleted}, expected True"
        print("[PASS] Physically exists with is_deleted=True")

        # Clean up
        session.delete(raw_hw)
        session.commit()
        print("[PASS] Cleaned up test data")


if __name__ == "__main__":
    verify()
