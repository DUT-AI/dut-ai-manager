from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission
from sqlmodel import Session, select, desc


class HomeworkRepository(BaseRepository[Homework]):
    """Repository for Homework operations"""

    def __init__(self, session: Session):
        super().__init__(session, Homework)

    def get_all(
        self, skip: int = 0, limit: int = 100, deleted: bool = False
    ) -> List[Homework]:
        """Get all homeworks with pagination, sorted by created_at desc"""
        statement = (
            select(Homework)
            .where(Homework.is_deleted == deleted)
            .order_by(desc(Homework.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def restore(self, homework_id: int) -> Optional[Homework]:
        """Restore a soft-deleted homework"""
        homework = self.session.exec(
            select(Homework).where(
                Homework.id == homework_id, Homework.is_deleted == True
            )
        ).first()

        if homework:
            homework.is_deleted = False
            self.session.add(homework)
            self.session.commit()
            self.session.refresh(homework)
            return homework
        return None

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Homework]:
        """Get homeworks assigned to a specific user via HomeworkSubmission"""
        statement = (
            select(Homework)
            .join(HomeworkSubmission, Homework.id == HomeworkSubmission.homework_id)
            .where(HomeworkSubmission.owner_id == user_id)
            .where(Homework.is_deleted == False)
            .order_by(desc(Homework.created_at))
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
