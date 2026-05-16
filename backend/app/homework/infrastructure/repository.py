from typing import Any, cast

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql.functions import count

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.entity import HomeworkStatus
from app.homework.domain.entity import HomeworkSubmission as HomeworkSubmissionEntity
from app.homework.infrastructure.model import HomeworkModel, HomeworkSubmissionModel


class HomeworkRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_unsubmitted_by_user(self, user_id: int) -> list[HomeworkEntity]:
        """Lấy danh sách các bài tập mà user CHƯA nộp thành công."""
        # Join Homework with Submissions for this user
        statement = (
            select(HomeworkModel)
            .options(
                selectinload(HomeworkModel.submissions).joinedload(
                    HomeworkSubmissionModel.owner
                )
            )
            .join(
                HomeworkSubmissionModel,
                HomeworkModel.id == HomeworkSubmissionModel.homework_id,
            )
            .where(
                HomeworkSubmissionModel.owner_id == user_id,
                cast(
                    Any, HomeworkSubmissionModel.status == HomeworkStatus.NOT_SUBMITTED
                ),
                HomeworkModel.is_deleted == False,
            )
            .order_by(desc(HomeworkModel.deadline))
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> list[HomeworkEntity]:
        """Get all homeworks optionally with pagination."""
        statement = (
            select(HomeworkModel)
            .options(
                selectinload(HomeworkModel.submissions).joinedload(
                    HomeworkSubmissionModel.owner
                )
            )
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
            .options(
                selectinload(HomeworkModel.submissions).joinedload(
                    HomeworkSubmissionModel.owner
                )
            )
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
            model.description = homework.description
            model.deadline = homework.deadline
            model.file_url = homework.file_url
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

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> list[HomeworkEntity]:
        statement = (
            select(HomeworkModel)
            .options(
                selectinload(HomeworkModel.submissions).joinedload(
                    HomeworkSubmissionModel.owner
                )
            )
            .join(
                HomeworkSubmissionModel,
                HomeworkModel.id == HomeworkSubmissionModel.homework_id,
            )
            .where(HomeworkSubmissionModel.owner_id == user_id)
            .where(HomeworkModel.is_deleted == False)  # noqa: E712
            .order_by(desc(HomeworkModel.created_at))
            .offset(skip)
            .limit(limit)
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]


class HomeworkSubmissionRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, submission_id: int) -> HomeworkSubmissionEntity | None:
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.id == submission_id,
                HomeworkSubmissionModel.is_deleted == False,  # noqa: E712
            )
            .options(joinedload(HomeworkSubmissionModel.owner))
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None

    def create(self, submission: HomeworkSubmissionEntity) -> HomeworkSubmissionEntity:
        model = HomeworkSubmissionModel.from_entity(submission)
        self.session.add(model)
        self.session.flush()
        return model.to_entity()

    def bulk_create(self, submissions: list[HomeworkSubmissionEntity]) -> None:
        models = [HomeworkSubmissionModel.from_entity(s) for s in submissions]
        for model in models:
            self.session.add(model)
        self.session.flush()

    def update(
        self, submission: HomeworkSubmissionEntity
    ) -> HomeworkSubmissionEntity | None:
        statement = select(HomeworkSubmissionModel).where(
            HomeworkSubmissionModel.id == submission.id
        )
        model = self.session.scalars(statement).first()
        if model:
            model.link = submission.link
            model.status = submission.status
            model.is_late = submission.is_late
            # Grading fields
            model.is_pass = submission.is_pass
            model.score = submission.score
            model.feedback = submission.feedback
            model.score_details = submission.score_details
            model.plagiarism_info = submission.plagiarism_info
            model.is_plagiarized = submission.is_plagiarized
            model.plagiarized_from_user_id = submission.plagiarized_from_user_id

            self.session.add(model)
            self.session.flush()
            model_eager = self.session.scalars(
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
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            return True
        return False

    def get_by_homework_and_user(
        self, homework_id: int, user_id: int
    ) -> HomeworkSubmissionEntity | None:
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.is_deleted == False,  # noqa: E712
                HomeworkSubmissionModel.homework_id == homework_id,
                HomeworkSubmissionModel.owner_id == user_id,
            )
            .options(joinedload(HomeworkSubmissionModel.owner))
        )
        model = self.session.scalars(statement).first()
        return model.to_entity() if model else None

    def get_all_by_homework(
        self, homework_id: int, skip: int = 0, limit: int = 100
    ) -> list[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .where(HomeworkSubmissionModel.is_deleted == False)  # noqa: E712
            .where(HomeworkSubmissionModel.homework_id == homework_id)
            .options(joinedload(HomeworkSubmissionModel.owner))
            .order_by(HomeworkSubmissionModel.created_at)
            .offset(skip)
            .limit(limit)
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_owner_ids_by_homework(self, homework_id: int) -> list[int]:
        statement = select(HomeworkSubmissionModel.owner_id).where(
            HomeworkSubmissionModel.is_deleted == False,  # noqa: E712
            HomeworkSubmissionModel.homework_id == homework_id,
        )
        return list(self.session.scalars(statement).all())

    def delete_by_homework_and_owner(self, homework_id: int, owner_id: int) -> bool:
        statement = select(HomeworkSubmissionModel).where(
            HomeworkSubmissionModel.is_deleted == False,  # noqa: E712
            HomeworkSubmissionModel.homework_id == homework_id,
            HomeworkSubmissionModel.owner_id == owner_id,
        )
        model = self.session.scalars(statement).first()
        if model:
            model.is_deleted = True
            self.session.add(model)
            return True
        return False

    def get_all_by_user(self, user_id: int) -> list[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .where(
                HomeworkSubmissionModel.is_deleted == False,  # noqa: E712
                HomeworkSubmissionModel.owner_id == user_id,
            )
            .options(
                joinedload(HomeworkSubmissionModel.owner),
                joinedload(HomeworkSubmissionModel.homework),
            )
        )
        models = self.session.scalars(statement).all()
        entities = []
        for m in models:
            e = m.to_entity()
            if hasattr(m, "homework") and m.homework:
                e.homework = m.homework.to_entity()
            entities.append(e)
        return entities

    def get_not_submitted_for_deadline_date(
        self, target_date: Any
    ) -> list[HomeworkSubmissionEntity]:
        statement = (
            select(HomeworkSubmissionModel)
            .join(
                HomeworkModel,
                HomeworkSubmissionModel.homework_id == HomeworkModel.id,
            )
            .where(
                HomeworkSubmissionModel.is_deleted == False,  # noqa: E712
                cast(
                    Any, HomeworkSubmissionModel.status == HomeworkStatus.NOT_SUBMITTED
                ),
                func.date(HomeworkModel.deadline) == target_date,
            )
            .options(
                joinedload(HomeworkSubmissionModel.owner),
                joinedload(HomeworkSubmissionModel.homework),
            )
        )
        models = self.session.scalars(statement).unique().all()
        entities = []
        for m in models:
            e = m.to_entity()
            if hasattr(m, "homework") and m.homework:
                e.homework = m.homework.to_entity()
            entities.append(e)
        return entities

    def get_unsubmitted_counts_per_user(self) -> dict[int, int]:
        statement = (
            select(HomeworkSubmissionModel.owner_id, count(HomeworkSubmissionModel.id))
            .join(
                HomeworkModel,
                HomeworkSubmissionModel.homework_id == HomeworkModel.id,
            )
            .where(
                HomeworkSubmissionModel.is_deleted == False,
                cast(
                    Any, HomeworkSubmissionModel.status == HomeworkStatus.NOT_SUBMITTED
                ),
                HomeworkModel.is_deleted == False,
            )
            .group_by(HomeworkSubmissionModel.owner_id)
        )
        results = self.session.execute(statement).all()
        return {r[0]: r[1] for r in results}
