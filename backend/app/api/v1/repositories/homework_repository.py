from typing import List, Optional

from app.api.v1.repositories.base import BaseRepository
from app.models.homework import Homework, HomeworkAssignee
from sqlmodel import Session, select


class HomeworkRepository(BaseRepository[Homework]):
    """Repository for Homework operations"""

    def __init__(self, session: Session):
        super().__init__(session, Homework)

    def create_with_assignees(
        self, homework: Homework, assignee_ids: List[int]
    ) -> Homework:
        """Create homework and assign to users"""
        self.session.add(homework)
        self.session.flush()  # Get ID

        for user_id in assignee_ids:
            assignee = HomeworkAssignee(homework_id=homework.id, user_id=user_id)
            self.session.add(assignee)

        self.session.commit()
        self.session.refresh(homework)
        return homework

    def assign_users(self, homework_id: int, user_ids: List[int]):
        """Assign users to an existing homework"""
        # First remove existing assignments if needed or just add new ones?
        # A simple strategy: clear and re-add for Update operation
        statement = select(HomeworkAssignee).where(
            HomeworkAssignee.homework_id == homework_id
        )
        existing = self.session.exec(statement).all()
        for item in existing:
            self.session.delete(item)

        for user_id in user_ids:
            assignee = HomeworkAssignee(homework_id=homework_id, user_id=user_id)
            self.session.add(assignee)

        self.session.commit()

    def get_assigned_to_user(
        self, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[Homework]:
        """Get homeworks assigned to a specific user"""
        # Logic:
        # 1. Homeworks targeted specifically to user (in HomeworkAssignee table)
        # 2. Homeworks with NO assignees (Public homeworks) - if that's the rule.
        # But User request implies "specific members". If table is empty, maybe it means NO ONE assigned yet?
        # Let's assume if assignees exist, it's restricted. If not, maybe everyone?
        # Or let's stick to strict assignment for now based on user request.
        # Actually user said "giao cụ thể cho thành viên nào nữa".

        # Query: Joined with Assignees filtered by user_id OR Homeworks with no assignees?
        # Let's start with strict assignment + empty check if needed.

        # Simple Join
        statement = (
            select(Homework)
            .join(HomeworkAssignee, Homework.id == HomeworkAssignee.homework_id)
            .where(HomeworkAssignee.user_id == user_id)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).all())
