import os
import sys
from datetime import date, datetime, time

# Ensure we can import app
sys.path.append(os.getcwd())

from app.api.v1.repositories.bonus_point_repository import BonusPointRepository
from app.api.v1.repositories.permission_request_repository import \
    PermissionRequestRepository
from app.api.v1.repositories.violation_repository import ViolationRepository
from app.core.database import engine
from app.models.bonus_points import BonusPoint
from app.models.permission_request import PermissionRequest, RequestCategory
from app.models.violation import Violation
from sqlmodel import Session


def verify_bonus_point(session):
    print("\n[VERIFY] BonusPoint")
    repo = BonusPointRepository(session)
    # Create
    item = BonusPoint(user_id=1, points=5, reason="Test Restore", date=datetime.now())
    created = repo.create(item)
    print(f"[PASS] Created BonusPoint ID: {created.id}")

    # Delete
    repo.delete(created)
    print("[PASS] Deleted BonusPoint")

    # Verify in Deleted
    deleted_list = repo.get_all(deleted=True)
    assert any(
        x.id == created.id for x in deleted_list
    ), "BonusPoint not found in deleted list"
    print("[PASS] Found in deleted list")

    # Restore
    restored = repo.restore(created.id)
    assert restored.is_deleted is False, "BonusPoint not restored"
    print("[PASS] Restored BonusPoint")

    # Verify in Normal
    normal_list = repo.get_all(deleted=False)
    assert any(
        x.id == created.id for x in normal_list
    ), "BonusPoint not in normal list after restore"
    print("[PASS] Back in normal list")

    # Cleanup
    session.delete(restored)
    session.commit()


def verify_violation(session):
    print("\n[VERIFY] Violation")
    repo = ViolationRepository(session)
    # Create
    item = Violation(
        user_id=1, reason="Test Restore Violation", date=datetime.now(), minus_points=2
    )
    created = repo.create(item)
    print(f"[PASS] Created Violation ID: {created.id}")

    # Delete
    repo.delete(created)
    print("[PASS] Deleted Violation")

    # Verify in Deleted
    deleted_list = repo.get_all(deleted=True)
    assert any(
        x.id == created.id for x in deleted_list
    ), "Violation not found in deleted list"
    print("[PASS] Found in deleted list")

    # Restore
    restored = repo.restore(created.id)
    assert restored.is_deleted is False, "Violation not restored"
    print("[PASS] Restored Violation")

    # Verify in Normal
    normal_list = repo.get_all(deleted=False)
    assert any(
        x.id == created.id for x in normal_list
    ), "Violation not in normal list after restore"
    print("[PASS] Back in normal list")

    # Cleanup
    session.delete(restored)
    session.commit()


def verify_permission(session):
    print("\n[VERIFY] PermissionRequest")
    repo = PermissionRequestRepository(session)
    # Create
    item = PermissionRequest(
        created_by=1,
        category=RequestCategory.ABSENCE,
        note="Test Restore Permission",
        date=date.today(),
        start_time=time(12, 0),
        end_time=time(13, 0),
    )
    created = repo.create(item)
    print(f"[PASS] Created PermissionRequest ID: {created.id}")

    # Delete
    repo.delete(created)
    print("[PASS] Deleted PermissionRequest")

    # Verify in Deleted
    deleted_list = repo.get_all(deleted=True)
    assert any(
        x.id == created.id for x in deleted_list
    ), "PermissionRequest not found in deleted list"

    # Also verify get_all defaults to deleted=False
    normal_list_check = repo.get_all()
    assert not any(
        x.id == created.id for x in normal_list_check
    ), "Deleted PermissionRequest found in default list"
    print("[PASS] Found in deleted list and NOT in normal list")

    # Restore
    restored = repo.restore(created.id)
    assert restored.is_deleted is False, "PermissionRequest not restored"
    print("[PASS] Restored PermissionRequest")

    # Verify in Normal
    normal_list = repo.get_all(deleted=False)
    assert any(
        x.id == created.id for x in normal_list
    ), "PermissionRequest not in normal list after restore"
    print("[PASS] Back in normal list")

    # Cleanup
    session.delete(restored)
    session.commit()


def run_verify():
    with Session(engine) as session:
        try:
            # We assume user_id=1 exists. If not, catching IntegrityError might be needed
            # But let's hope data exists.
            verify_bonus_point(session)
            verify_violation(session)
            verify_permission(session)
            print("\n[SUCCESS] All checks passed!")
        except Exception as e:
            print(f"\n[FAILED] {e}")
            # Raise to see full traceback if needed
            raise


if __name__ == "__main__":
    run_verify()
