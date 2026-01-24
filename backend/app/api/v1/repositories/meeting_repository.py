from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select

from app.api.v1.repositories.base import BaseRepository
from app.models.meeting import Meeting, MeetingParticipant


class MeetingRepository(BaseRepository[Meeting]):
    def __init__(self, session: Session):
        super().__init__(session, Meeting)

    def get_with_participants(self, meeting_id: int) -> Optional[Meeting]:
        statement = (
            select(Meeting)
            .where(Meeting.id == meeting_id)
            .options(
                joinedload(Meeting.participants).joinedload(MeetingParticipant.user)
            )
        )
        return self.session.exec(statement).first()

    def get_all_with_participants(
        self, skip: int = 0, limit: int = 100
    ) -> List[Meeting]:
        statement = (
            select(Meeting)
            .options(
                joinedload(Meeting.participants).joinedload(MeetingParticipant.user)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).unique().all())

    def get_by_date(self, target_date: date) -> List[Meeting]:
        statement = (
            select(Meeting)
            .where(func.date(Meeting.start_time) == target_date)
            .options(
                joinedload(Meeting.participants).joinedload(MeetingParticipant.user)
            )
        )
        return list(self.session.exec(statement).unique().all())


class MeetingParticipantRepository(BaseRepository[MeetingParticipant]):
    def __init__(self, session: Session):
        super().__init__(session, MeetingParticipant)

    def get_by_meeting_and_user(
        self, meeting_id: int, user_id: int
    ) -> Optional[MeetingParticipant]:
        statement = (
            select(MeetingParticipant)
            .where(MeetingParticipant.meeting_id == meeting_id)
            .where(MeetingParticipant.user_id == user_id)
        )
        return self.session.exec(statement).first()

    def get_by_meeting(self, meeting_id: int) -> List[MeetingParticipant]:
        statement = (
            select(MeetingParticipant)
            .where(MeetingParticipant.meeting_id == meeting_id)
            .options(joinedload(MeetingParticipant.user))
        )
        return list(self.session.exec(statement).all())
