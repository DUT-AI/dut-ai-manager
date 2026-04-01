from typing import List, Optional

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkStatus
from app.homework.domain.entity import \
  HomeworkSubmission as HomeworkSubmissionEntity
from app.homework.infrastructure.model import (HomeworkModel,
                                               HomeworkSubmissionModel)
from sqlalchemy import func
from sqlalchemy.orm import contains_eager, joinedload
from sqlmodel import Session, desc, select


class HomeworkRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[HomeworkEntity]:
        """Get all homeworks optionally with pagination."""
        statement = (
            select(HomeworkModel)
            .where(HomeworkModel.is_deleted == deleted)
            .order_by(desc(HomeworkModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        models = self.session.exec(statement).all()
        return [m.to_entity() for m in models]

    def get_by_id(self, homework_id: int) -> Optional[HomeworkEntity]:
        statement = select(HomeworkModel).where(
            HomeworkModel.id == homework_id, HomeworkModel.is_deleted == False
        )
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def create(self, homework: HomeworkEntity) -> HomeworkEntity:
        model = HomeworkModel.from_entity(homework)
        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def update(self, homework: HomeworkEntity) -> Optional[HomeworkEntity]:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework.id)
        model = self.session.exec(statement).first()
        if model:
            model.title = homework.title
            model.description = homework.description
            model.deadline = homework.deadline
            model.file_url = homework.file_url
            self.session.add(model)
            self.session.flush()
            return model.to_entity()
        return None

    def delete_by_id(self, homework_id: int) -> bool:
        statement = select(HomeworkModel).where(HomeworkModel.id == homework_id)
        model = self.session.exec(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            return True
        return False

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[HomeworkEntity]:
        statement = (
            select(HomeworkModel)
            .join(
                HomeworkSubmissionModel,
                HomeworkModel.id == HomeworkSubmissionModel.homework_id,
            )
            .where(HomeworkSubmissionModel.owner_id == user_id)
            .where(HomeworkModel.is_deleted == False)
            .order_by(desc(HomeworkModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        models = self.session.exec(statement).all()
        return [m.to_entity() for m in models]


class HomeworkSubmissionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, submission_id: int) -> Optional[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.id == submission_id,
                HomeworkSubmissionModel.is_deleted == False,
            )
            .options(joinedload(HomeworkSubmissionModel.owner))
        )
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def create(self, submission: HomeworkSubmissionEntity) -> HomeworkSubmissionEntity:
        model = HomeworkSubmissionModel.from_entity(submission)
        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def update(
        self, submission: HomeworkSubmissionEntity
    ) -> Optional[HomeworkSubmissionEntity]:
        statement = select(HomeworkSubmissionModel).where(
            HomeworkSubmissionModel.id == submission.id
        )
        model = self.session.exec(statement).first()
        if model:
            model.link = submission.link
            model.status = submission.status
            model.is_late = submission.is_late
            self.session.add(model)
            self.session.flush()
            model_eager = self.session.exec(
                select(HomeworkSubmissionModel)
                .where(HomeworkSubmissionModel.id == model.id)
                .options(joinedload(HomeworkSubmissionModel.owner))
            ).first()
            return model_eager.to_entity() if model_eager else None
        return None

    def delete(self, submission_id: int) -> bool:
        statement = select(HomeworkSubmissionModel).where(
            HomeworkSubmissionModel.id == submission_id
        )
        model = self.session.exec(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            return True
        return False

    def get_by_homework_and_user(
        self, homework_id: int, user_id: int
    ) -> Optional[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.is_deleted == False,
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.owner_id == user_id,
            )
            .options(joinedload(HomeworkSubmissionModel.owner))
        )
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def get_all_by_homework(
        self, homework_id: int, skip: int = 0, limit: int = 100
    ) -> List[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .where(HomeworkSubmissionModel.is_deleted == False)
            .where(HomeworkSubmissionModel.homework_id == homework_id)
            .options(joinedload(HomeworkSubmissionModel.owner))
            .order_by(HomeworkSubmissionModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        models = self.session.exec(statement).all()
        return [m.to_entity() for m in models]

    def get_owner_ids_by_homework(self, homework_id: int) -> List[int]:
        statement = select(HomeworkSubmissionModel.owner_id).where(
            HomeworkSubmissionModel.is_deleted == False,
            HomeworkSubmissionModel.homework_id == homework_id,
        )
        return list(self.session.exec(statement).all())

    def delete_by_homework_and_owner(self, homework_id: int, owner_id: int) -> bool:
        statement = select(HomeworkSubmissionModel).where(
            HomeworkSubmissionModel.is_deleted == False,
            HomeworkSubmissionModel.homework_id == homework_id,
            HomeworkSubmissionModel.owner_id == owner_id,
        )
        model = self.session.exec(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            return True
        return False

    def get_all_by_user(self, user_id: int) -> List[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.is_deleted == False,
                HomeworkSubmissionModel.owner_id == user_id,
            )
            .options(
                joinedload(HomeworkSubmissionModel.owner),
                joinedload(HomeworkSubmissionModel.homework),
            )
        )
        models = self.session.exec(statement).all()
        # In this specific case where we also want homework eagerly loaded for get_unsubmitted_by_user
        # We might need to attach homework entity to submission entity if needed.
        # But wait, HomeworkSubmission domain entity doesn't have a `homework` field.
        # Let's adjust entity to include a reference to `Homework` if needed, or simply return a pair.
        entities = []
        for m in models:
            e = m.to_entity()
            # Workaround: attach homework temporarily or we can fetch them dynamically
            # The current codebase relies on sumission.homework in get_unsubmitted_by_user
            setattr(e, "homework", m.homework.to_entity() if m.homework else None)
            entities.append(e)
        return entities

    def get_not_submitted_for_deadline_date(
        self, target_date
    ) -> List[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .join(
                HomeworkModel, HomeworkSubmissionModel.homework_id == HomeworkModel.id
            )
            .where(
                HomeworkSubmissionModel.is_deleted == False,
                HomeworkSubmissionModel.status == HomeworkStatus.NOT_SUBMITTED,
                func.date(HomeworkModel.deadline) == target_date,
            )
            .options(
                joinedload(HomeworkSubmissionModel.owner),
                joinedload(HomeworkSubmissionModel.homework),
            )
        )
        models = self.session.exec(statement).unique().all()
        entities = []
        for m in models:
            e = m.to_entity()
            setattr(e, "homework", m.homework.to_entity() if m.homework else None)
            entities.append(e)
        return entities
