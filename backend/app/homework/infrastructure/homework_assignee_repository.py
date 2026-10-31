from datetime import UTC, date, datetime
from typing import NamedTuple
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.homework.domain.value_objects import DueHomeworkAssignment
from app.homework.infrastructure.model import HomeworkAssigneeModel, HomeworkModel
from app.shared.domain.datetime_types import ensure_utc
from app.user.infrastructure.model import UserModel


class AssigneeUserInfo(NamedTuple):
    user_id: int
    name: str
    avatar_url: str | None
    deadline: datetime


class HomeworkAssigneeRepository:
    """Repository chuyên trách quản lý bảng phân công học viên homework_assignees."""

    def __init__(self, session: Session):
        self.session = session

    def sync_assignees(
        self,
        homework_id: int,
        assignee_ids: list[int] | None,
        default_deadline: datetime | None = None,
    ) -> None:
        """Đồng bộ danh sách học viên được giao bài tập."""
        if assignee_ids is None:
            return

        existing_assignees = {
            a.user_id: a
            for a in self.session.scalars(
                select(HomeworkAssigneeModel).where(
                    HomeworkAssigneeModel.homework_id == homework_id
                )
            ).all()
        }
        new_uids = set(assignee_ids)
        # Xoá các assignee không còn trong danh sách
        for uid, a in existing_assignees.items():
            if uid not in new_uids:
                self.session.delete(a)

        added_uids = [uid for uid in new_uids if uid not in existing_assignees]
        clean_dl: datetime | None = None
        if added_uids:
            if default_deadline is not None:
                clean_dl = ensure_utc(default_deadline)
            elif existing_assignees:
                clean_dl = min(a.deadline for a in existing_assignees.values())
            else:
                raise ValueError(
                    f"Không thể gán học viên vào bài tập {homework_id} khi thiếu deadline"
                )

        # Thêm hoặc giữ nguyên
        for uid in new_uids:
            if uid in existing_assignees:
                existing_assignees[uid].is_deleted = False
                if default_deadline is not None:
                    existing_assignees[uid].deadline = ensure_utc(default_deadline)
            else:
                assert clean_dl is not None
                self.session.add(
                    HomeworkAssigneeModel(
                        homework_id=homework_id,
                        user_id=uid,
                        deadline=clean_dl,
                    )
                )
        self.session.flush()

    def assign_users(
        self,
        homework_id: int,
        user_ids: set[int] | list[int],
        deadline: datetime,
    ) -> None:
        """Gán danh sách học viên vào bài tập kèm deadline cụ thể."""
        clean_deadline = ensure_utc(deadline)
        existing_stmt = select(HomeworkAssigneeModel).where(
            HomeworkAssigneeModel.homework_id == homework_id,
            HomeworkAssigneeModel.user_id.in_(user_ids),
        )
        existing = {a.user_id: a for a in self.session.scalars(existing_stmt).all()}

        for uid in set(user_ids):
            if uid in existing:
                existing[uid].is_deleted = False
                existing[uid].deadline = clean_deadline
            else:
                self.session.add(
                    HomeworkAssigneeModel(
                        homework_id=homework_id,
                        user_id=uid,
                        deadline=clean_deadline,
                    )
                )
        self.session.flush()

    def get_user_deadline(self, homework_id: int, user_id: int) -> datetime | None:
        """Lấy hạn nộp cá nhân của học viên đối với một bài tập."""
        statement = select(HomeworkAssigneeModel.deadline).where(
            HomeworkAssigneeModel.homework_id == homework_id,
            HomeworkAssigneeModel.user_id == user_id,
            HomeworkAssigneeModel.is_deleted == False,
        )
        return self.session.scalar(statement)

    def update_deadline(
        self, homework_id: int, user_id: int, new_deadline: datetime
    ) -> bool:
        """Cập nhật deadline cá nhân của học viên."""
        statement = select(HomeworkAssigneeModel).where(
            HomeworkAssigneeModel.homework_id == homework_id,
            HomeworkAssigneeModel.user_id == user_id,
            HomeworkAssigneeModel.is_deleted == False,
        )
        assignee = self.session.scalar(statement)
        if assignee:
            assignee.deadline = ensure_utc(new_deadline)
            self.session.flush()
            return True
        return False

    def get_by_deadline_date(
        self, target_date: date | datetime
    ) -> list[DueHomeworkAssignment]:
        """
        Lấy danh sách các phân công bài tập có deadline trong ngày target_date (theo giờ Việt Nam UTC+7).
        Dùng khoảng UTC [start_utc, end_utc] để tận dụng index ix_homework_assignees_deadline.
        """
        target_day = (
            target_date.date() if isinstance(target_date, datetime) else target_date
        )
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        start_vn = datetime.combine(target_day, datetime.min.time(), tzinfo=vn_tz)
        end_vn = datetime.combine(target_day, datetime.max.time(), tzinfo=vn_tz)
        start_utc = start_vn.astimezone(UTC)
        end_utc = end_vn.astimezone(UTC)

        statement = (
            select(
                HomeworkAssigneeModel.homework_id,
                HomeworkAssigneeModel.user_id,
                HomeworkModel.title,
                HomeworkAssigneeModel.deadline,
                HomeworkModel.requires_coding,
                HomeworkModel.requires_game,
            )
            .join(HomeworkModel, HomeworkAssigneeModel.homework_id == HomeworkModel.id)
            .where(
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkModel.is_deleted == False,
                HomeworkAssigneeModel.deadline >= start_utc,
                HomeworkAssigneeModel.deadline <= end_utc,
            )
        )
        rows = self.session.execute(statement).all()
        return [
            DueHomeworkAssignment(
                homework_id=r[0],
                user_id=r[1],
                homework_title=r[2],
                deadline=r[3],
                requires_coding=r[4],
                requires_game=r[5],
            )
            for r in rows
        ]

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
        """Lấy danh sách học viên được giao bài tập kèm tên, avatar và deadline cá nhân."""
        statement = (
            select(
                HomeworkAssigneeModel.user_id,
                UserModel.name,
                UserModel.avatar_url,
                HomeworkAssigneeModel.deadline,
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
            AssigneeUserInfo(
                user_id=r[0], name=r[1], avatar_url=r[2], deadline=r[3]
            )
            for r in rows
        ]

    def get_assigned_homework_ids(self, user_id: int) -> list[int]:
        """Lấy danh sách homework_id được giao cho một user cụ thể."""
        statement = select(HomeworkAssigneeModel.homework_id).where(
            HomeworkAssigneeModel.user_id == user_id,
            HomeworkAssigneeModel.is_deleted == False,
        )
        return list(self.session.scalars(statement).all())

    def get_user_deadlines_for_homeworks(
        self, homework_ids: list[int], user_id: int
    ) -> dict[int, datetime]:
        """Lấy hạn nộp cá nhân của user cho danh sách bài tập."""
        if not homework_ids:
            return {}
        statement = select(
            HomeworkAssigneeModel.homework_id, HomeworkAssigneeModel.deadline
        ).where(
            HomeworkAssigneeModel.homework_id.in_(homework_ids),
            HomeworkAssigneeModel.user_id == user_id,
            HomeworkAssigneeModel.is_deleted == False,
        )
        rows = self.session.execute(statement).all()
        return {r[0]: r[1] for r in rows if r[1] is not None}

    def get_min_deadlines_by_homework_ids(
        self, homework_ids: list[int]
    ) -> dict[int, datetime]:
        """Lấy hạn nộp sớm nhất của từng bài tập trong danh sách ID."""
        if not homework_ids:
            return {}
        from sqlalchemy import func

        statement = (
            select(
                HomeworkAssigneeModel.homework_id,
                func.min(HomeworkAssigneeModel.deadline),
            )
            .where(
                HomeworkAssigneeModel.homework_id.in_(homework_ids),
                HomeworkAssigneeModel.is_deleted == False,
            )
            .group_by(HomeworkAssigneeModel.homework_id)
        )
        rows = self.session.execute(statement).all()
        return {r[0]: r[1] for r in rows if r[1] is not None}

    def add_assignees(
        self,
        homework_id: int,
        user_ids: list[int],
        deadline: datetime,
    ) -> None:
        """Thêm các assignee mới nếu chưa tồn tại."""
        clean_dl = ensure_utc(deadline)
        existing = self.get_assigned_user_ids(homework_id)
        for uid in set(user_ids):
            if uid not in existing:
                self.session.add(
                    HomeworkAssigneeModel(
                        homework_id=homework_id, user_id=uid, deadline=clean_dl
                    )
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

    def get_distinct_past_deadline_dates(self, before_date: date) -> list[date]:
        """Lấy danh sách các ngày có deadline trong quá khứ theo giờ VN."""
        vn_tz = ZoneInfo("Asia/Ho_Chi_Minh")
        end_vn = datetime.combine(before_date, datetime.max.time(), tzinfo=vn_tz)
        end_utc = end_vn.astimezone(UTC)

        statement = (
            select(HomeworkAssigneeModel.deadline)
            .where(
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkAssigneeModel.deadline <= end_utc,
            )
            .distinct()
        )
        deadlines = self.session.scalars(statement).all()
        distinct_dates = set()
        for dl in deadlines:
            if dl is not None:
                dl_vn = dl if dl.tzinfo is not None else dl.replace(tzinfo=UTC)
                distinct_dates.add(dl_vn.astimezone(vn_tz).date())
        return sorted(list(distinct_dates))
