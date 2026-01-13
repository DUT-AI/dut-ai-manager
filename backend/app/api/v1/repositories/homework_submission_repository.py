from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models import HomeworkSubmission
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class HomeworkSubmissionRepository(BaseRepository[HomeworkSubmission]):
    """Repository for HomeworkSubmission operations"""

    def __init__(self, session: Session):
        super().__init__(session, HomeworkSubmission)

    def get_by_homework_and_user(
        self, homework_id: int, user_id: int
    ) -> Optional[HomeworkSubmission]:
        """Get submission for a homework by a specific user (owner)"""
        statement = select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id,
            HomeworkSubmission.owner_id == user_id,
        )
        return self.session.exec(statement).first()

    def get_all_by_homework(
        self, homework_id: int, skip: int = 0, limit: int = 100
    ) -> List[HomeworkSubmission]:
        """Get all submissions for a homework"""
        statement = (
            select(HomeworkSubmission)
            .where(HomeworkSubmission.homework_id == homework_id)
            .options(joinedload(HomeworkSubmission.owner))
            .order_by(HomeworkSubmission.created_at)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())

    def get_owner_ids_by_homework(self, homework_id: int) -> List[int]:
        """Get all owner_ids for a homework"""
        statement = select(HomeworkSubmission.owner_id).where(
            HomeworkSubmission.homework_id == homework_id
        )
        return list(self.session.exec(statement).all())

    def delete_by_homework_and_owner(self, homework_id: int, owner_id: int) -> bool:
        """Delete a submission by homework and owner"""
        statement = select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == homework_id,
            HomeworkSubmission.owner_id == owner_id,
        )
        submission = self.session.exec(statement).first()
        if submission:
            self.session.delete(submission)
            self.session.commit()
            return True
        return False
