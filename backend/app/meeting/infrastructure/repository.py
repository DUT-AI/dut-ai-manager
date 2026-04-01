from datetime import date, datetime
from typing import List, Optional

from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy import extract, func
from sqlalchemy.orm import contains_eager, joinedload
from sqlmodel import Session, select

from ..domain.entity import Meeting as DomainMeeting
from ..domain.entity import MeetingParticipant as DomainParticipant
from ..domain.entity import UserRef
from .model import Meeting as ORMMeeting
from .model import MeetingParticipant as ORMParticipant


class MeetingRepository(BaseRepository[ORMMeeting]):
    def __init__(self, session: Session):
        super().__init__(session, ORMMeeting)

    def _to_domain(self, orm: ORMMeeting) -> DomainMeeting:
        participants = []
        for p in orm.participants:
            user_ref = None
            if p.user:
                user_ref = UserRef(
                    id=p.user.id, name=p.user.name, avatar_url=p.user.avatar_url
                )

            participants.append(
                DomainParticipant(
                    id=p.id,
                    meeting_id=p.meeting_id,
                    user_id=p.user_id,
                    status=p.status,
                    check_in_at=p.check_in_at,
                    link_image=p.link_image,
                    user=user_ref,
                )
            )

        return DomainMeeting(
            id=orm.id,
            title=orm.title,
            content=orm.content,
            start_time=orm.start_time,
            end_time=orm.end_time,
            require_check_in=orm.require_check_in,
            participants=participants,
        )

    def get_with_participants(self, meeting_id: int) -> Optional[DomainMeeting]:
        statement = (
            select(ORMMeeting)
            .outerjoin(
                ORMParticipant,
                (ORMMeeting.id == ORMParticipant.meeting_id)
                & (ORMParticipant.is_deleted == False),
            )
            .where(
                ORMMeeting.is_deleted == False,
                ORMMeeting.id == meeting_id,
            )
            .options(
                contains_eager(ORMMeeting.participants).joinedload(ORMParticipant.user)
            )
        )
        orm = self.session.exec(statement).unique().first()
        return self._to_domain(orm) if orm else None

    def get_all_with_participants(
        self,
        skip: int = 0,
        limit: int = 100,
        month: Optional[int] = None,
        year: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DomainMeeting]:
        query = select(ORMMeeting).where(ORMMeeting.is_deleted == False)

        if month:
            query = query.where(extract("month", ORMMeeting.start_time) == month)
        if year:
            query = query.where(extract("year", ORMMeeting.start_time) == year)
        if start_date:
            query = query.where(func.date(ORMMeeting.start_time) >= start_date)
        if end_date:
            query = query.where(func.date(ORMMeeting.start_time) <= end_date)

        statement = (
            query.outerjoin(
                ORMParticipant,
                (ORMMeeting.id == ORMParticipant.meeting_id)
                & (ORMParticipant.is_deleted == False),
            )
            .options(
                contains_eager(ORMMeeting.participants).joinedload(ORMParticipant.user)
            )
            .order_by(ORMMeeting.start_time)
            .offset(skip)
            .limit(limit)
        )
        orms = self.session.exec(statement).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_by_date(self, target_date: date) -> List[DomainMeeting]:
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted == False,
                func.date(ORMMeeting.start_time) == target_date,
            )
            .options(
                joinedload(ORMMeeting.participants).joinedload(ORMParticipant.user)
            )
        )
        orms = self.session.exec(statement).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_concurrent_participants_count(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_meeting_id: Optional[int] = None,
    ) -> int:
        statement = (
            select(func.count(ORMParticipant.id))
            .join(ORMMeeting)
            .where(
                ORMMeeting.is_deleted == False,
                ORMParticipant.is_deleted == False,
                ORMMeeting.start_time < end_time,
                ORMMeeting.end_time > start_time,
            )
        )

        if exclude_meeting_id:
            statement = statement.where(ORMMeeting.id != exclude_meeting_id)

        result = self.session.exec(statement).first()
        return result if result else 0

    def save(self, domain: DomainMeeting) -> DomainMeeting:
        if domain.id:
            orm = self.session.get(ORMMeeting, domain.id)
            if not orm:
                orm = ORMMeeting(id=domain.id)
        else:
            orm = ORMMeeting()

        orm.title = domain.title
        orm.content = domain.content
        orm.start_time = domain.start_time
        orm.end_time = domain.end_time
        orm.require_check_in = domain.require_check_in

        # Update participants separately or via cascade?
        # For simplicity in this Clean Arch refactor, we usually use orm update if id exists
        if not orm.id:
            self.session.add(orm)
            self.session.flush()  # get id
        else:
            self.session.add(orm)

        domain.id = orm.id
        return domain

    def delete(self, meeting_id: int) -> bool:
        orm = self.session.get(ORMMeeting, meeting_id)
        if not orm:
            return False
        orm.is_deleted = True
        self.session.add(orm)
        return True


class ParticipantRepository(BaseRepository[ORMParticipant]):
    def __init__(self, session: Session):
        super().__init__(session, ORMParticipant)

    def _to_domain(self, orm: ORMParticipant) -> DomainParticipant:
        user_ref = None
        if orm.user:
            user_ref = UserRef(
                id=orm.user.id, name=orm.user.name, avatar_url=orm.user.avatar_url
            )

        return DomainParticipant(
            id=orm.id,
            meeting_id=orm.meeting_id,
            user_id=orm.user_id,
            status=orm.status,
            check_in_at=orm.check_in_at,
            link_image=orm.link_image,
            user=user_ref,
        )

    def get_by_meeting_and_user(
        self, meeting_id: int, user_id: int
    ) -> Optional[DomainParticipant]:
        statement = (
            select(ORMParticipant)
            .where(
                ORMParticipant.is_deleted == False,
                ORMParticipant.meeting_id == meeting_id,
                ORMParticipant.user_id == user_id,
            )
            .options(
                joinedload(ORMParticipant.user), joinedload(ORMParticipant.meeting)
            )
        )
        orm = self.session.exec(statement).first()
        return self._to_domain(orm) if orm else None

    def save(self, domain: DomainParticipant) -> DomainParticipant:
        if domain.id:
            orm = self.session.get(ORMParticipant, domain.id)
            if not orm:
                orm = ORMParticipant(id=domain.id)
        else:
            orm = ORMParticipant()

        orm.meeting_id = domain.meeting_id
        orm.user_id = domain.user_id
        orm.status = domain.status
        orm.check_in_at = domain.check_in_at
        orm.link_image = domain.link_image

        self.session.add(orm)
        self.session.flush()
        domain.id = orm.id
        return domain

    def delete_by_meeting(self, meeting_id: int) -> bool:
        statement = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id
        )
        orms = self.session.exec(statement).all()
        for orm in orms:
            orm.is_deleted = True
            self.session.add(orm)
        return True
