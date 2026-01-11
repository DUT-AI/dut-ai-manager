from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models.homework import Homework
from app.models.homework_submission import HomeworkSubmission
from sqlmodel import Session, select


class HomeworkRepository(BaseRepository[Homework]):
    """Repository for Homework operations"""

    def __init__(self, session: Session):
        super().__init__(session, Homework)

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Homework]:
        """Get homeworks assigned to a specific user via HomeworkSubmission"""
        statement = (
            select(Homework)
            .join(HomeworkSubmission, Homework.id == HomeworkSubmission.homework_id)
            .where(HomeworkSubmission.owner_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
