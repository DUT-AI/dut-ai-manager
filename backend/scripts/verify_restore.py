import sys
import os
from datetime import datetime

# Ensure we can import app
sys.path.append(os.getcwd())

from sqlmodel import Session, select
from app.core.database import engine
from app.models.homework import Homework
from app.api.v1.repositories.homework_repository import HomeworkRepository


def verify_restore():
    print("Starting Restore Feature Verification")
    with Session(engine) as session:
        repo = HomeworkRepository(session)

        # 1. Create a homework
        hw = Homework(
            title="Restore Verification Task",
            deadline=datetime.now(),
            description="Testing restore",
        )
        created_hw = repo.create(hw)
        hw_id = created_hw.id
        print(f"[PASS] Created homework with ID: {hw_id}")

        # 2. Delete it
        repo.delete(created_hw)
        print("[PASS] Deleted homework")

        session.expire_all()

        # 3. Verify it's gone from normal get_all
        all_hw = repo.get_all(deleted=False)
        assert not any(
            h.id == hw_id for h in all_hw
        ), "Deleted homework should not be in normal list"
        print("[PASS] Homework not in normal list")

        # 4. Verify it's in deleted list
        deleted_hw = repo.get_all(deleted=True)
        assert any(
            h.id == hw_id for h in deleted_hw
        ), "Deleted homework should be in deleted list"
        print("[PASS] Homework found in deleted list")

        # 5. Restore it
        restored = repo.restore(hw_id)
        assert restored is not None, "Restore returned None"
        assert (
            restored.is_deleted is False
        ), "Restored homework is_deleted should be False"
        print("[PASS] Restored homework successfully")

        session.expire_all()

        # 6. Verify it's back in normal list
        all_hw_after = repo.get_all(deleted=False)
        assert any(
            h.id == hw_id for h in all_hw_after
        ), "Restored homework should be in normal list"
        print("[PASS] Homework back in normal list")

        # 7. Verify it's gone from deleted list
        deleted_hw_after = repo.get_all(deleted=True)
        assert not any(
            h.id == hw_id for h in deleted_hw_after
        ), "Restored homework should not be in deleted list"
        print("[PASS] Homework gone from deleted list")

        # Cleanup
        repo.delete(restored)  # Soft delete again
        # Hard delete manually for cleanup if needed, or leave it soft deleted
        # Let's hard delete to keep DB clean
        session.delete(restored)
        session.commit()
        print("[PASS] Cleanup done")


if __name__ == "__main__":
    verify_restore()
