from datetime import date
from typing import List, Optional
from sqlalchemy import extract


from sqlalchemy import func
from sqlalchemy.orm import contains_eager, joinedload
from sqlmodel import Session, select

from app.api.v1.repositories.base import BaseRepository
from app.models.meeting import Meeting, MeetingParticipant


class MeetingRepository(BaseRepository[Meeting]):
    def __init__(self, session: Session):
        super().__init__(session, Meeting)

    def get_with_participants(self, meeting_id: int) -> Optional[Meeting]:
        statement = (
            select(Meeting)
            .outerjoin(
                MeetingParticipant,
                (Meeting.id == MeetingParticipant.meeting_id)
                & (MeetingParticipant.is_deleted == False),
            )
            .where(
                Meeting.is_deleted == False,
                Meeting.id == meeting_id,
            )
            .options(
                contains_eager(Meeting.participants).joinedload(MeetingParticipant.user)
            )
        )
        return self.session.exec(statement).unique().first()

    def get_all_with_participants(
        self,
        skip: int = 0,
        limit: int = 100,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> List[Meeting]:
        query = select(Meeting).where(Meeting.is_deleted == False)

        if month:
            query = query.where(extract("month", Meeting.start_time) == month)
        if year:
            query = query.where(extract("year", Meeting.start_time) == year)

        statement = (
            query.outerjoin(
                MeetingParticipant,
                (Meeting.id == MeetingParticipant.meeting_id)
                & (MeetingParticipant.is_deleted == False),
            )
            .options(
                contains_eager(Meeting.participants).joinedload(MeetingParticipant.user)
            )
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).unique().all())

    def get_by_date(self, target_date: date) -> List[Meeting]:
        statement = select(Meeting).where(
            Meeting.is_deleted == False,
            func.date(Meeting.start_time) == target_date,
        )
        return list(self.session.exec(statement).unique().all())


class MeetingParticipantRepository(BaseRepository[MeetingParticipant]):
    def __init__(self, session: Session):
        super().__init__(session, MeetingParticipant)

    def get_by_meeting_and_user(
        self, meeting_id: int, user_id: int
    ) -> Optional[MeetingParticipant]:
        statement = select(MeetingParticipant).where(
            MeetingParticipant.is_deleted == False,
            MeetingParticipant.meeting_id == meeting_id,
            MeetingParticipant.user_id == user_id,
        )
        return self.session.exec(statement).first()

    def get_by_meeting(self, meeting_id: int) -> List[MeetingParticipant]:
        statement = (
            select(MeetingParticipant)
            .where(
                MeetingParticipant.is_deleted == False,
                MeetingParticipant.meeting_id == meeting_id,
            )
            .options(joinedload(MeetingParticipant.user))
        )
        return list(self.session.exec(statement).all())
