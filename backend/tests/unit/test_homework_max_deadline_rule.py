"""
Unit test kiểm tra nguyên tắc Max Deadline Rule (Bảo lưu quyền lợi tối đa).
Đảm bảo khi Admin cập nhật bài tập, hạn hoãn cá nhân của học sinh không bị đè bẹp.
"""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.homework.application.delete_homework_use_case import DeleteHomeworkUseCase
from app.homework.application.dtos import HomeworkUpdate
from app.homework.application.update_homework_use_case import UpdateHomeworkUseCase
from app.homework.domain.entity import Homework
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.homework.infrastructure.model import (
    HomeworkAssigneeModel,
    HomeworkModel,
    HomeworkSubmissionModel,
)
from app.homework.infrastructure.quiz_api import QuizApiClient
from app.shared.infrastructure.base_model import Base
from app.user.infrastructure.model import UserModel


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    # Tạo các bảng liên quan
    Base.metadata.create_all(
        engine,
        tables=[
            UserModel.__table__,
            HomeworkModel.__table__,
            HomeworkAssigneeModel.__table__,
            HomeworkSubmissionModel.__table__,
        ],
    )
    with Session(engine) as session:
        yield session


def test_sync_assignees_preserves_extended_deadline(db_session: Session):
    """
    Test Case 1: Học sinh A có hạn hoãn 15/11, học sinh B có hạn gốc 10/11.
    Admin cập nhật deadline chung lớp thành 12/11:
    - B được nâng lên 12/11 (12/11 > 10/11).
    - A giữ nguyên 15/11 (12/11 < 15/11, không bị đè bẹp hạn hoãn).
    """
    hw_repo = HomeworkRepository(db_session)
    repo = HomeworkAssigneeRepository(db_session)
    hw = hw_repo.create(Homework(title="HW 1", slug="hw-1"))
    hw_id = hw.id
    assert hw_id is not None
    uid_a = 101  # Đã xin hoãn
    uid_b = 102  # Chưa xin hoãn

    initial_base = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    postponed_dl = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)

    # Khởi tạo ban đầu
    repo.assign_users(hw_id, [uid_a, uid_b], initial_base)
    # Học sinh A xin hoãn thành công tới 15/11
    repo.update_deadline(hw_id, uid_a, postponed_dl)

    expected_a = repo.get_user_deadline(hw_id, uid_a)
    assert expected_a is not None

    # Admin cập nhật hạn lớp lên 12/11
    new_class_dl = datetime(2026, 11, 12, 12, 0, tzinfo=UTC)
    repo.sync_assignees(hw_id, [uid_a, uid_b], default_deadline=new_class_dl)

    # Học sinh A không bị kéo lùi về 12/11 (vẫn giữ hạn hoãn 15/11)
    assert repo.get_user_deadline(hw_id, uid_a) == expected_a
    # Học sinh B được nâng lên hạn mới 12/11 (> initial_base)
    assert repo.get_user_deadline(hw_id, uid_b) > initial_base
    assert repo.get_user_deadline(hw_id, uid_a) > repo.get_user_deadline(hw_id, uid_b)


def test_sync_assignees_elevates_when_class_deadline_is_farther(db_session: Session):
    """
    Test Case 2: Cả lớp được dời hạn lên 20/11 (xa hơn cả hạn hoãn 15/11 của A):
    - Cả A và B đều được nâng lên 20/11 để hưởng quyền lợi chung của lớp.
    """
    hw_repo = HomeworkRepository(db_session)
    repo = HomeworkAssigneeRepository(db_session)
    hw = hw_repo.create(Homework(title="HW 2", slug="hw-2"))
    hw_id = hw.id
    assert hw_id is not None
    uid_a = 201

    postponed_dl = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    repo.assign_users(hw_id, [uid_a], postponed_dl)
    prev_dl = repo.get_user_deadline(hw_id, uid_a)

    farther_dl = datetime(2026, 11, 20, 12, 0, tzinfo=UTC)
    repo.sync_assignees(hw_id, [uid_a], default_deadline=farther_dl)

    assert repo.get_user_deadline(hw_id, uid_a) > prev_dl


def test_sync_assignees_force_override_works(db_session: Session):
    """
    Test Case 3: Khi Admin cố tình ép ghi đè toàn bộ (force_override=True),
    deadline của mọi học sinh bị reset theo hạn mới kể cả hạn hoãn.
    """
    hw_repo = HomeworkRepository(db_session)
    repo = HomeworkAssigneeRepository(db_session)
    hw = hw_repo.create(Homework(title="HW 3", slug="hw-3"))
    hw_id = hw.id
    assert hw_id is not None
    uid_a = 301

    postponed_dl = datetime(2026, 11, 15, 12, 0, tzinfo=UTC)
    repo.assign_users(hw_id, [uid_a], postponed_dl)
    prev_dl = repo.get_user_deadline(hw_id, uid_a)

    forced_dl = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    repo.sync_assignees(hw_id, [uid_a], default_deadline=forced_dl, force_override=True)

    # Khi ép ghi đè, deadline bị rút ngắn về 10/11 (< prev_dl 15/11)
    assert repo.get_user_deadline(hw_id, uid_a) < prev_dl


@pytest.mark.asyncio
async def test_update_homework_use_case_protects_individual_deadlines():
    """
    Test Case 4: Kiểm tra UseCase UpdateHomeworkUseCase chuyển đúng force_override flag
    cho AssigneeRepository.
    """
    hw_repo = MagicMock()
    assignee_repo = MagicMock()
    quiz_api = MagicMock(spec=QuizApiClient)

    existing_hw = Homework(
        id=10,
        title="Python Bài 1",
        slug="python-01",
        requires_coding=True,
        requires_game=False,
    )
    hw_repo.get_by_id.return_value = existing_hw
    hw_repo.save.return_value = existing_hw

    quiz_api.get_lesson_metadata = AsyncMock(
        return_value={"slug": "python-01", "has_coding": True, "has_game": False}
    )

    use_case = UpdateHomeworkUseCase(hw_repo, quiz_api, assignee_repo)

    # 1. Update bình thường (force_override_deadlines=False)
    new_dl = datetime(2026, 11, 12, 0, 0, tzinfo=UTC)
    assignee_repo.get_assigned_user_ids.return_value = {1, 2}

    await use_case.execute(
        homework_id=10,
        data=HomeworkUpdate(
            deadline=new_dl,
            force_override_deadlines=False,
        ),
    )
    assignee_repo.assign_users.assert_called_once_with(
        10, {1, 2}, deadline=new_dl, force_override=False
    )

    # 2. Update với force_override_deadlines=True
    assignee_repo.assign_users.reset_mock()
    await use_case.execute(
        homework_id=10,
        data=HomeworkUpdate(
            deadline=new_dl,
            force_override_deadlines=True,
        ),
    )
    assignee_repo.assign_users.assert_called_once_with(
        10, {1, 2}, deadline=new_dl, force_override=True
    )


def test_hard_delete_homework_cascades_and_removes_assignees(db_session: Session):
    """
    Test Case 5: Xóa cứng (Hard Delete) bài tập sẽ tự động Cascade xóa sạch
    toàn bộ assignees trong cơ sở dữ liệu. Không còn bản ghi mồ côi.
    """
    hw_repo = HomeworkRepository(db_session)
    assignee_repo = HomeworkAssigneeRepository(db_session)

    # 1. Tạo bài tập
    created_hw = hw_repo.create(
        Homework(
            title="Bài tập Cấu trúc dữ liệu",
            slug="dsa-01",
            requires_coding=True,
            requires_game=False,
        )
    )
    hw_id = created_hw.id
    assert hw_id is not None

    # 2. Gán 3 học viên vào bài tập
    dl = datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
    assignee_repo.assign_users(hw_id, [501, 502, 503], dl)
    assert len(assignee_repo.get_assigned_user_ids(hw_id)) == 3

    # 3. Thực hiện Hard Delete qua Use Case
    del_uc = DeleteHomeworkUseCase(hw_repo)
    result = del_uc.execute(hw_id)
    assert result is True

    # 4. Kiểm tra bài tập đã bị xóa hoàn toàn khỏi DB
    assert hw_repo.get_by_id(hw_id) is None

    # 5. Kiểm tra toàn bộ assignees bị Cascade xóa sạch
    assert assignee_repo.get_assigned_user_ids(hw_id) == set()
    from sqlalchemy import select

    remaining_rows = db_session.scalars(
        select(HomeworkAssigneeModel).where(HomeworkAssigneeModel.homework_id == hw_id)
    ).all()
    assert len(remaining_rows) == 0
