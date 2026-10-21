from typing import NamedTuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.homework.infrastructure.model import HomeworkAssigneeModel
from app.user.infrastructure.model import UserModel


class AssigneeUserInfo(NamedTuple):
    user_id: int
    name: str
    avatar_url: str | None


class HomeworkAssigneeRepository:
    """Repository chuyên trách quản lý bảng phân công học viên homework_assignees."""

    def __init__(self, session: Session):
        self.session = session

    def sync_assignees(self, homework_id: int, assignee_ids: list[int] | None) -> None:
        """Đồng bộ danh sách học viên được giao bài tập."""
        if assignee_ids is not None:
            existing_assignees = self.session.scalars(
                select(HomeworkAssigneeModel).where(
                    HomeworkAssigneeModel.homework_id == homework_id
                )
            ).all()
            for a in existing_assignees:
                self.session.delete(a)
            for uid in set(assignee_ids):
                self.session.add(
                    HomeworkAssigneeModel(homework_id=homework_id, user_id=uid)
                )
            self.session.flush()

    def get_assigned_user_ids(self, homework_id: int) -> set[int]:
        """Lấy danh sách user_id được phân làm homework."""
        direct_uids = set(
            self.session.scalars(
                select(HomeworkAssigneeModel.user_id).where(
                    HomeworkAssigneeModel.homework_id == homework_id,
                    HomeworkAssigneeModel.is_deleted == False,
                )
            ).all()
        )
        return direct_uids

    def get_assignees_with_user_info(self, homework_id: int) -> list[AssigneeUserInfo]:
        """Lấy danh sách học viên được giao bài tập kèm tên và avatar bằng 1 câu SQL JOIN duy nhất."""
        statement = (
            select(
                HomeworkAssigneeModel.user_id,
                UserModel.name,
                UserModel.avatar_url,
            )
            .join(UserModel, HomeworkAssigneeModel.user_id == UserModel.id)
            .where(
                HomeworkAssigneeModel.homework_id == homework_id,
                HomeworkAssigneeModel.is_deleted == False,
                UserModel.is_deleted == False,
            )
            .order_by(UserModel.name.asc())
        )
        rows = self.session.execute(statement).all()
        return [
            AssigneeUserInfo(user_id=r[0], name=r[1], avatar_url=r[2]) for r in rows
        ]

    def get_assigned_homework_ids(self, user_id: int) -> list[int]:
        """Lấy danh sách homework_id được giao cho một user cụ thể."""
        statement = select(HomeworkAssigneeModel.homework_id).where(
            HomeworkAssigneeModel.user_id == user_id,
            HomeworkAssigneeModel.is_deleted == False,
        )
        return list(self.session.scalars(statement).all())

    def add_assignees(self, homework_id: int, user_ids: list[int]) -> None:
        """Thêm các assignee mới nếu chưa tồn tại."""
        existing = self.get_assigned_user_ids(homework_id)
        for uid in set(user_ids):
            if uid not in existing:
                self.session.add(
                    HomeworkAssigneeModel(homework_id=homework_id, user_id=uid)
                )
        self.session.flush()

    def remove_assignees(self, homework_id: int, user_ids: list[int]) -> None:
        """Xóa assignee khỏi bài tập."""
        if not user_ids:
            return
        statement = select(HomeworkAssigneeModel).where(
            HomeworkAssigneeModel.homework_id == homework_id,
            HomeworkAssigneeModel.user_id.in_(user_ids),
        )
        assignees = self.session.scalars(statement).all()
        for a in assignees:
            self.session.delete(a)
        self.session.flush()
