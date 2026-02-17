from datetime import date, datetime
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
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Meeting]:
        query = select(Meeting).where(Meeting.is_deleted == False)

        if month:
            query = query.where(extract("month", Meeting.start_time) == month)
        if year:
            query = query.where(extract("year", Meeting.start_time) == year)
        if start_date:
            query = query.where(func.date(Meeting.start_time) >= start_date)
        if end_date:
            query = query.where(func.date(Meeting.start_time) <= end_date)

        statement = (
            query.outerjoin(
                MeetingParticipant,
                (Meeting.id == MeetingParticipant.meeting_id)
                & (MeetingParticipant.is_deleted == False),
            )
            .options(
                contains_eager(Meeting.participants).joinedload(MeetingParticipant.user)
            )
            .order_by(Meeting.start_time)
            .offset(skip)
            .limit(limit)
        )
        return list(self.session.exec(statement).unique().all())

    def get_by_date(self, target_date: date) -> List[Meeting]:
        statement = (
            select(Meeting)
            .where(
                Meeting.is_deleted == False,
                func.date(Meeting.start_time) == target_date,
            )
            .options(
                joinedload(Meeting.participants).joinedload(MeetingParticipant.user)
            )
        )
        return list(self.session.exec(statement).unique().all())

    def get_ended_meetings_requiring_checkin(self, target_date: date) -> List[Meeting]:
        """Get meetings that ended today and require check-in."""
        now = datetime.now()
        statement = (
            select(Meeting)
            .where(
                Meeting.is_deleted == False,
                Meeting.require_check_in == True,
                func.date(Meeting.start_time) == target_date,
                Meeting.end_time <= now,
            )
            .options(
                joinedload(Meeting.participants).joinedload(MeetingParticipant.user)
            )
        )
        return list(self.session.exec(statement).unique().all())
        return list(self.session.exec(statement).unique().all())

    def get_concurrent_participants_count(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_meeting_id: Optional[int] = None,
    ) -> int:
        """Get the total number of participants in meetings that overlap with the given time range."""
        statement = (
            select(func.count(MeetingParticipant.id))
            .join(Meeting)
            .where(
                Meeting.is_deleted == False,
                MeetingParticipant.is_deleted == False,
                # Overlap condition: (StartA < EndB) and (EndA > StartB)
                Meeting.start_time < end_time,
                Meeting.end_time > start_time,
            )
        )

        if exclude_meeting_id:
            statement = statement.where(Meeting.id != exclude_meeting_id)

        result = self.session.exec(statement).first()
        return result if result else 0


class MeetingParticipantRepository(BaseRepository[MeetingParticipant]):
    def __init__(self, session: Session):
        super().__init__(session, MeetingParticipant)

    def get_by_meeting_and_user(
        self, meeting_id: int, user_id: int
    ) -> Optional[MeetingParticipant]:
        statement = select(MeetingParticipant).where(
            MeetingParticipant.is_deleted == False,
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
                MeetingParticipant.is_deleted == False,
                MeetingParticipant.meeting_id == meeting_id,
            )
            .options(joinedload(MeetingParticipant.user))
        )
        return list(self.session.exec(statement).all())
