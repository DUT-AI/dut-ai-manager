from typing import Any, cast

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.model import (
    HomeworkAssigneeModel,
    HomeworkModel,
)
from app.shared.domain.query_support import QuerySupport, apply_query_support


class HomeworkRepository:
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

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        statement = (
            select(HomeworkModel)
            .where(
                HomeworkModel.id == homework_id,
                HomeworkModel.is_deleted == False,  # noqa: E712
            )
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None

    def create(self, homework: HomeworkEntity) -> HomeworkEntity:
        model = HomeworkModel.from_entity(homework)
        self.session.add(model)
        self.session.flush()

        if homework.assignee_ids:
            for uid in homework.assignee_ids:
                self.session.add(HomeworkAssigneeModel(homework_id=model.id, user_id=uid))
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
            if model.id is not None:
                self.sync_assignees(model.id, homework.assignee_ids)
            return model.to_entity()
        return None

    def sync_assignees(
        self, homework_id: int, assignee_ids: list[int] | None
    ) -> None:
        if assignee_ids is not None:
            existing_assignees = self.session.scalars(
                select(HomeworkAssigneeModel).where(HomeworkAssigneeModel.homework_id == homework_id)
            ).all()
            for a in existing_assignees:
                self.session.delete(a)
            for uid in set(assignee_ids):
                self.session.add(HomeworkAssigneeModel(homework_id=homework_id, user_id=uid))
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

    def get_by_deadline_date(self, target_date: Any) -> list[HomeworkEntity]:
        statement = (
            select(HomeworkModel)
            .where(
                HomeworkModel.is_deleted == False,  # noqa: E712
                func.date(HomeworkModel.deadline) == target_date,
            )
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def delete_by_id(self, homework_id: int) -> bool:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework_id)
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            self.session.flush()
            return True
        return False

    def save(self, homework: HomeworkEntity) -> HomeworkEntity:
        if homework.id:
            res = self.update(homework)
            return res if res else homework
        return self.create(homework)

    def delete(self, homework_id: int) -> bool:
        return self.delete_by_id(homework_id)

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
