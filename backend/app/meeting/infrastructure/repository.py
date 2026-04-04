from datetime import date, datetime
from typing import Any, List, Optional, cast

from app.shared.infrastructure.base_repository import BaseRepository
from sqlalchemy import and_, case, desc, func
from sqlalchemy.orm import contains_eager, joinedload
from sqlmodel import Session, select
from app.shared.domain.query_support import QuerySupport, apply_query_support

from ..domain.entity import Meeting as DomainMeeting
from ..domain.entity import MeetingParticipant as DomainParticipant
from ..domain.entity import UserRef
from .model import Meeting as ORMMeeting
from .model import MeetingParticipant as ORMParticipant


class MeetingRepository(BaseRepository[ORMMeeting, DomainMeeting]):
    def __init__(self, session: Session):
        super().__init__(session, ORMMeeting)

    def _to_domain(self, orm: ORMMeeting) -> DomainMeeting:
        participants = []
        for p in orm.participants:
            user_ref = None
            if p.user and p.user.id is not None:
                user_ref = UserRef(
                    id=p.user.id, name=p.user.name or "", avatar_url=p.user.avatar_url
                )

            participants.append(
                DomainParticipant(
                    id=p.id,
                    meeting_id=p.meeting_id,
                    user_id=p.user_id if p.user_id is not None else 0,
                    status=p.status,
                    check_in_at=p.check_in_at,
                    link_image=p.link_image,
                    user=user_ref,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
            )

        return DomainMeeting(
            id=orm.id,
            title=orm.title,
            start_time=orm.start_time,
            end_time=orm.end_time,
            content=orm.content,
            require_check_in=orm.require_check_in,
            participants=participants,
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def get_with_participants(self, meeting_id: int) -> Optional[DomainMeeting]:
        statement = (
            select(ORMMeeting)
            .outerjoin(
                ORMParticipant,
                cast(Any, ORMMeeting.id == ORMParticipant.meeting_id)
                & (cast(Any, ORMParticipant.is_deleted).is_(False)),
            )
            .where(
                cast(Any, ORMMeeting.is_deleted).is_(False),
                ORMMeeting.id == meeting_id,
            )
            .options(
                contains_eager(cast(Any, ORMMeeting.participants)).joinedload(
                    cast(Any, ORMParticipant.user)
                )
            )
        )
        orm = self.session.exec(statement).unique().first()
        return self._to_domain(orm) if orm else None

    def get_all_with_participants(
        self,
        query_support: Optional[QuerySupport] = None,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
        month: Optional[int] = None,
        year: Optional[int] = None,
    ) -> List[DomainMeeting]:
        from app.shared.application.query_support_utils import build_query_support
        from app.shared.domain.query_support import FilterCriterion, FilterOperator

        if not query_support:
            filters = []
            if month:
                filters.append(
                    FilterCriterion(
                        field="start_time",
                        operator=FilterOperator.MONTH_EQ,
                        value=month,
                    )
                )
            if year:
                filters.append(
                    FilterCriterion(
                        field="start_time", operator=FilterOperator.YEAR_EQ, value=year
                    )
                )
            query_support = build_query_support(filters=filters, skip=skip, limit=limit)

        stmt = (
            select(ORMMeeting)
            .where(
                cast(Any, getattr(ORMMeeting, "is_deleted") == deleted)
            )  # noqa: E712
            .outerjoin(
                ORMParticipant,
                cast(
                    Any,
                    getattr(ORMParticipant, "meeting_id") == getattr(ORMMeeting, "id"),
                ),
            )
            .where(
                cast(Any, getattr(ORMParticipant, "is_deleted")).is_(False),
            )
            .options(
                contains_eager(cast(Any, ORMMeeting.participants)).joinedload(
                    cast(Any, ORMParticipant.user)
                ),
            )
        )

        stmt = apply_query_support(stmt, ORMMeeting, query_support)

        orms = self.session.exec(stmt).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_participating_meetings(
        self, user_id: int, month: Optional[int] = None, year: Optional[int] = None
    ) -> List[DomainMeeting]:
        """Get meetings where user is a participant, filtered by month/year."""
        from app.shared.application.query_support_utils import build_query_support
        from app.shared.domain.query_support import FilterCriterion, FilterOperator

        filters = []
        if month:
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.MONTH_EQ, value=month
                )
            )
        if year:
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.YEAR_EQ, value=year
                )
            )

        qs = build_query_support(filters=filters, limit=1000)

        stmt = (
            select(ORMMeeting)
            .join(ORMParticipant, cast(Any, ORMMeeting.id == ORMParticipant.meeting_id))
            .where(
                cast(Any, ORMMeeting.is_deleted == False),  # noqa: E712
                cast(Any, ORMParticipant.user_id == user_id),
                cast(Any, ORMParticipant.is_deleted == False),  # noqa: E712
            )
        )

        stmt = apply_query_support(stmt, ORMMeeting, qs)
        orms = self.session.exec(stmt).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_by_date(self, target_date: date) -> List[DomainMeeting]:
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),  # type: ignore
                func.date(ORMMeeting.start_time) == target_date,
            )
            .options(
                joinedload(cast(Any, ORMMeeting.participants)).joinedload(
                    cast(Any, ORMParticipant.user)
                )
            )
        )
        orms = self.session.exec(statement).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_domain_for_check_in(self, meeting_id: int) -> Optional[DomainMeeting]:
        """Meeting tối thiểu cho luật trễ / event (không load participants)."""
        orm = self.session.get(ORMMeeting, meeting_id)
        if not orm or orm.is_deleted:
            return None
        return DomainMeeting(
            id=orm.id,
            title=orm.title,
            content=orm.content,
            start_time=orm.start_time,
            end_time=orm.end_time,
            require_check_in=orm.require_check_in,
            participants=[],
            created_at=orm.created_at,
            updated_at=orm.updated_at,
        )

    def get_concurrent_participants_count(
        self,
        start_time: datetime,
        end_time: datetime,
        exclude_meeting_id: Optional[int] = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(ORMParticipant)
            .join(ORMMeeting)
            .where(
                cast(Any, ORMMeeting.is_deleted).is_(False),
                cast(Any, ORMParticipant.is_deleted).is_(False),
                ORMMeeting.start_time < end_time,
                ORMMeeting.end_time > start_time,
            )
        )

        if exclude_meeting_id:
            statement = statement.where(ORMMeeting.id != exclude_meeting_id)

        result = self.session.exec(statement).first()
        return result if result else 0

    def save(self, domain: DomainMeeting) -> DomainMeeting:
        is_new = domain.id is None
        if domain.id:
            orm = self.session.get(ORMMeeting, domain.id)
            if not orm:
                orm = ORMMeeting(
                    id=domain.id,
                    title=domain.title,
                    start_time=domain.start_time,
                    end_time=domain.end_time,
                )
        else:
            orm = ORMMeeting(
                title=domain.title,
                start_time=domain.start_time,
                end_time=domain.end_time,
            )

        orm.title = domain.title
        orm.content = domain.content
        orm.start_time = domain.start_time
        orm.end_time = domain.end_time
        orm.require_check_in = domain.require_check_in

        self.session.add(orm)
        self.session.flush()
        domain.id = orm.id

        if is_new and domain.participants:
            for dp in domain.participants:
                po = ORMParticipant(
                    meeting_id=orm.id,
                    user_id=dp.user_id,
                    status=dp.status,
                    check_in_at=dp.check_in_at,
                    link_image=dp.link_image,
                )
                self.session.add(po)
            self.session.flush()

        reloaded = self.get_with_participants(orm.id)
        return reloaded if reloaded is not None else domain

    def delete(self, meeting_id: int) -> bool:
        orm = self.session.get(ORMMeeting, meeting_id)
        if not orm:
            return False
        orm.is_deleted = True
        self.session.add(orm)
        return True


class ParticipantRepository(BaseRepository[ORMParticipant, DomainParticipant]):
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

    def find_participation_in_time_window(
        self,
        user_id: int,
        window_start: datetime,
        window_end: datetime,
        now: datetime,
    ) -> Optional[DomainParticipant]:
        """Participant của user trong meeting giao [window_start, window_end] với khung họp."""
        ongoing_expr = and_(
            cast(Any, ORMMeeting.start_time) <= now,
            cast(Any, ORMMeeting.end_time) >= now,
        )
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, cast(Any, ORMMeeting.id == ORMParticipant.meeting_id))
            .where(
                cast(Any, ORMMeeting.is_deleted).is_(False),
                cast(Any, ORMParticipant.is_deleted).is_(False),
                cast(Any, ORMParticipant.user_id) == user_id,
                ORMMeeting.start_time < window_end,
                ORMMeeting.end_time > window_start,
            )
            .options(
                joinedload(cast(Any, ORMParticipant.user)),
                joinedload(cast(Any, ORMParticipant.meeting)),
            )
            .order_by(
                case({ongoing_expr: 0}, else_=1), desc(cast(Any, ORMMeeting.start_time))
            )
            .limit(1)
        )
        orm = self.session.exec(stmt).first()
        return self._to_domain(orm) if orm else None

    def get_by_meeting_and_user(
        self, meeting_id: int, user_id: int
    ) -> Optional[DomainParticipant]:
        stmt = select(ORMParticipant).where(
            and_(
                getattr(ORMParticipant, "user_id") == user_id,
                getattr(ORMParticipant, "meeting_id") == meeting_id,
                getattr(ORMParticipant, "is_deleted") == False,  # noqa: E712
            )
        )
        orm = self.session.exec(stmt).first()
        return self._to_domain(orm) if orm else None

    def save(self, domain: DomainParticipant) -> DomainParticipant:
        if domain.id:
            orm = self.session.get(ORMParticipant, domain.id)
            if not orm:
                orm = ORMParticipant(
                    id=domain.id, meeting_id=domain.meeting_id, user_id=domain.user_id
                )
        else:
            orm = ORMParticipant(meeting_id=domain.meeting_id, user_id=domain.user_id)

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
