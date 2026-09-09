from typing import Any, cast

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql.functions import count

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.model import HomeworkModel


class HomeworkRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[HomeworkEntity]:
        """Get all homeworks optionally with pagination."""
        statement = (
            select(HomeworkModel)
            .where(HomeworkModel.is_deleted == deleted)
            .order_by(
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


    def delete_by_id(self, homework_id: int) -> bool:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework_id)
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
