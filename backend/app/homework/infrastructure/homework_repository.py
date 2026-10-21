from datetime import datetime
from typing import Any, cast

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.homework.domain.entity import (
    Homework as HomeworkEntity,
)
from app.homework.infrastructure.model import (
    HomeworkAssigneeModel,
    HomeworkModel,
)
from app.shared.domain.query_support import (
    QuerySupport,
    apply_filters_only,
    apply_query_support,
)


class HomeworkRepository:
    """Repository chuyên trách quản lý bảng bài tập homeworks và các truy vấn liên quan."""

    def __init__(self, session: Session):
        self.session = session

    def get_all(
        self,
        query_support: QuerySupport | None = None,
        skip: int = 0,
        limit: int = 100,
        deleted: bool = False,
    ) -> list[HomeworkEntity]:
        """Get all homeworks optionally with query support or pagination."""
        statement = select(HomeworkModel).where(HomeworkModel.is_deleted == deleted)
        if query_support:
            statement = apply_query_support(statement, HomeworkModel, query_support)
        else:
            statement = (
                statement.order_by(
                    desc(
                        cast(
                            Any,
                            (
                                HomeworkModel.updated_at
                                if deleted
                                else HomeworkModel.created_at
                            ),
                        )
                    )
                )
                .offset(skip)
                .limit(limit)
            )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_paged(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[HomeworkEntity], int]:
        """Get paginated homeworks and total count with optimized COUNT query."""
        count_stmt = select(func.count(HomeworkModel.id)).where(
            HomeworkModel.is_deleted == deleted
        )
        if query_support and query_support.filters:
            count_stmt = apply_filters_only(
                count_stmt, HomeworkModel, query_support.filters
            )
        total = self.session.scalar(count_stmt) or 0
        if total == 0:
            return [], 0

        statement = select(HomeworkModel).where(HomeworkModel.is_deleted == deleted)
        if query_support:
            statement = apply_query_support(statement, HomeworkModel, query_support)
            if not query_support.pagination:
                offset = (page - 1) * page_size
                statement = statement.offset(offset).limit(page_size)
        else:
            statement = statement.order_by(
                desc(
                    cast(
                        Any,
                        (
                            HomeworkModel.updated_at
                            if deleted
                            else HomeworkModel.created_at
                        ),
                    )
                )
            )
            offset = (page - 1) * page_size
            statement = statement.offset(offset).limit(page_size)

        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models], total

    def get_assigned_to_user_paged(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        deleted: bool = False,
    ) -> tuple[list[HomeworkEntity], int]:
        """Get paginated homeworks assigned to a specific user directly via SQL JOIN."""
        count_stmt = (
            select(func.count(HomeworkModel.id))
            .join(
                HomeworkAssigneeModel,
                HomeworkModel.id == HomeworkAssigneeModel.homework_id,
            )
            .where(
                HomeworkAssigneeModel.user_id == user_id,
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkModel.is_deleted == deleted,
            )
        )
        total = self.session.scalar(count_stmt) or 0
        if total == 0:
            return [], 0

        offset = (page - 1) * page_size
        statement = (
            select(HomeworkModel)
            .join(
                HomeworkAssigneeModel,
                HomeworkModel.id == HomeworkAssigneeModel.homework_id,
            )
            .where(
                HomeworkAssigneeModel.user_id == user_id,
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkModel.is_deleted == deleted,
            )
            .order_by(desc(HomeworkModel.created_at))
            .offset(offset)
            .limit(page_size)
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models], total

    def get_all_assigned_to_user(
        self,
        user_id: int,
        deleted: bool = False,
    ) -> list[HomeworkEntity]:
        """Get all homeworks assigned to a user directly via SQL JOIN."""
        statement = (
            select(HomeworkModel)
            .join(
                HomeworkAssigneeModel,
                HomeworkModel.id == HomeworkAssigneeModel.homework_id,
            )
            .where(
                HomeworkAssigneeModel.user_id == user_id,
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkModel.is_deleted == deleted,
            )
            .order_by(desc(HomeworkModel.created_at))
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_by_id(
        self, homework_id: int, deleted: bool = False
    ) -> HomeworkEntity | None:
        statement = select(HomeworkModel).where(
            HomeworkModel.id == homework_id,
            HomeworkModel.is_deleted == deleted,
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None

    def create(self, homework: HomeworkEntity) -> HomeworkEntity:
        model = HomeworkModel.from_entity(homework)
        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def update(self, homework: HomeworkEntity) -> HomeworkEntity | None:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework.id)
        model = self.session.scalars(statement).first()
        if model:
            model.title = homework.title
            model.deadline = homework.deadline
            model.link = homework.link
            model.slug = homework.slug
            self.session.add(model)
            self.session.flush()
            return model.to_entity()
        return None

    def get_by_deadline_date(self, target_date: Any) -> list[HomeworkEntity]:
        """Lấy danh sách bài tập active có deadline trong một ngày cụ thể."""
        target_day = (
            target_date.date() if isinstance(target_date, datetime) else target_date
        )
        statement = select(HomeworkModel).where(
            HomeworkModel.is_deleted == False,
            func.date(HomeworkModel.deadline) == target_day,
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def save(self, homework: HomeworkEntity) -> HomeworkEntity:
        if homework.id:
            res = self.update(homework)
            return res if res else homework
        return self.create(homework)

    def delete(self, homework_id: int) -> bool:
        return self.delete_by_id(homework_id)

    def delete_by_id(self, homework_id: int) -> bool:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework_id)
        model = self.session.scalars(statement).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def soft_delete(self, homework_id: int) -> bool:
        """Soft delete a homework: sets is_deleted to True."""
        statement = select(HomeworkModel).where(
            HomeworkModel.id == homework_id,
            HomeworkModel.is_deleted == False,
        )
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            self.session.flush()
            return True
        return False

    def restore(self, homework_id: int) -> HomeworkEntity | None:
        statement = select(HomeworkModel).where(
            HomeworkModel.id == homework_id,
            HomeworkModel.is_deleted == True,
        )
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = False
            self.session.add(model)
            self.session.flush()
            return model.to_entity()
        return None

    def get_by_slug(self, slug: str) -> HomeworkEntity | None:
        """Find active homework by slug."""
        statement = select(HomeworkModel).where(
            HomeworkModel.slug == slug,
            HomeworkModel.is_deleted == False,
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None
