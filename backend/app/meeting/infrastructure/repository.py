from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload

from app.shared.domain.query_support import QuerySupport, apply_query_support
from app.shared.infrastructure.base_repository import BaseRepository

from ..domain.entity import Meeting as DomainMeeting
from ..domain.entity import MeetingParticipant as DomainParticipant
from ..domain.entity import UserRef
from ..domain.value_objects import ParticipantStatus
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
                    check_out_at=p.check_out_at,
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

    def get_with_participants(self, meeting_id: int) -> DomainMeeting | None:
        statement = (
            select(ORMMeeting)
            .outerjoin(
                ORMParticipant,
                ORMMeeting.id
                == ORMParticipant.meeting_id & (ORMParticipant.is_deleted.is_(False)),
            )
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMMeeting.id == meeting_id,
            )
            .options(
                contains_eager(ORMMeeting.participants).joinedload(ORMParticipant.user)
            )
        )
        orm = self.session.scalars(statement).unique().first()
        return self._to_domain(orm) if orm else None

    def get_all_with_participants(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
        month: int | None = None,
        year: int | None = None,
    ) -> list[DomainMeeting]:
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
            .where(ORMMeeting.is_deleted == deleted)
            .outerjoin(
                ORMParticipant,
                cast(
                    Any,
                    ORMParticipant.meeting_id == ORMMeeting.id,
                ),
            )
            .where(
                ORMParticipant.is_deleted.is_(False),
            )
            .options(
                contains_eager(ORMMeeting.participants).joinedload(ORMParticipant.user),
            )
        )

        stmt = apply_query_support(stmt, ORMMeeting, query_support)

        orms = self.session.scalars(stmt).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_participating_meetings(
        self, user_id: int, month: int | None = None, year: int | None = None
    ) -> list[DomainMeeting]:
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
            .join(ORMParticipant, ORMMeeting.id == ORMParticipant.meeting_id)
            .where(
                ORMMeeting.is_deleted == False,  # noqa: E712
                ORMParticipant.user_id == user_id,
                ORMParticipant.is_deleted == False,  # noqa: E712
            )
        )

        stmt = apply_query_support(stmt, ORMMeeting, qs)
        orms = self.session.scalars(stmt).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_by_date(self, target_date: date) -> list[DomainMeeting]:
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                func.date(ORMMeeting.start_time) == target_date,
            )
            .options(
                joinedload(ORMMeeting.participants).joinedload(ORMParticipant.user)
            )
        )
        orms = self.session.scalars(statement).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_domain_for_check_in(self, meeting_id: int) -> DomainMeeting | None:
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
        exclude_meeting_id: int | None = None,
    ) -> int:
        statement = (
            select(func.count())
            .select_from(ORMParticipant)
            .join(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMParticipant.is_deleted.is_(False),
                ORMMeeting.start_time < end_time,
                ORMMeeting.end_time > start_time,
            )
        )

        if exclude_meeting_id:
            statement = statement.where(ORMMeeting.id != exclude_meeting_id)

        result = self.session.scalars(statement).first()
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
        elif (
            not is_new
            and hasattr(domain, "participants")
            and domain.participants is not None
        ):
            # Sync participants correctly by modifying the relationship list
            stmt = select(ORMParticipant).where(
                ORMParticipant.meeting_id == orm.id,
                ORMParticipant.is_deleted == False,  # noqa: E712
            )
            existing_participants = self.session.scalars(stmt).all()

            existing_user_ids = {p.user_id: p for p in existing_participants}
            new_user_ids = {p.user_id: p for p in domain.participants}

            # 1. Remove participants not in the new list
            for old_user_id, old_p in existing_user_ids.items():
                if old_user_id not in new_user_ids:
                    old_p.is_deleted = True
                    self.session.add(old_p)

            # 2. Add or update participants
            for new_user_id, new_p in new_user_ids.items():
                if new_user_id not in existing_user_ids:
                    # Check if there's a soft-deleted record we can reuse
                    stmt_deleted = select(ORMParticipant).where(
                        ORMParticipant.meeting_id == orm.id,
                        ORMParticipant.user_id == new_user_id,
                        ORMParticipant.is_deleted == True,  # noqa: E712
                    )
                    reusable = self.session.scalars(stmt_deleted).first()

                    if reusable:
                        reusable.is_deleted = False
                        reusable.status = new_p.status
                        reusable.check_in_at = new_p.check_in_at
                        reusable.link_image = new_p.link_image
                        self.session.add(reusable)
                    else:
                        po = ORMParticipant(
                            meeting_id=orm.id,
                            user_id=new_user_id,
                            status=new_p.status,
                            check_in_at=new_p.check_in_at,
                            link_image=new_p.link_image,
                        )
                        self.session.add(po)
                else:
                    existing = existing_user_ids[new_user_id]
                    # Update fields if they changed in the domain
                    existing.status = new_p.status
                    existing.check_in_at = new_p.check_in_at
                    existing.link_image = new_p.link_image
                    self.session.add(existing)

            self.session.flush()

        # Commit is handled by middleware, but we need to refresh to get updated participants for the return
        self.session.refresh(orm)
        return self._to_domain(orm)

    def delete(self, meeting_id: int) -> bool:
        orm = self.session.get(ORMMeeting, meeting_id)
        if not orm:
            return False
        orm.is_deleted = True
        self.session.add(orm)
        return True

    def get_present_participants_count(self, now: datetime) -> int:
        """
        N_current: người đã check-in và chưa check-out (hoặc check-out sau now).
        """
        stmt = select(func.count(ORMParticipant.id)).where(
            ORMParticipant.is_deleted.is_(False),
            ORMParticipant.check_in_at.is_not(None),
            or_(
                ORMParticipant.check_out_at.is_(None),
                ORMParticipant.check_out_at > now,
            ),
        )
        result = self.session.scalars(stmt).first()
        return result or 0

    def get_upcoming_participants_count(
        self, now: datetime, window_end: datetime
    ) -> int:
        """
        N_incoming: người có meeting bắt đầu trong [now, window_end].
        Chỉ tính participants chưa check-in.
        """
        from sqlalchemy.orm import aliased

        ParticipantAlias = aliased(ORMParticipant)

        stmt = (
            select(func.count(func.distinct(ParticipantAlias.user_id)))
            .join(ORMMeeting, ParticipantAlias.meeting_id == ORMMeeting.id)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ParticipantAlias.is_deleted.is_(False),
                ORMMeeting.start_time >= now,
                ORMMeeting.start_time <= window_end,
                ParticipantAlias.check_in_at.is_(None),
            )
        )
        result = self.session.scalars(stmt).first()
        return result or 0

    def get_departing_participants_count(
        self, now: datetime, window_end: datetime
    ) -> int:
        """
        N_outgoing: người đang có mặt và sẽ check-out trong [now, window_end].
        Chỉ tính những người đã check-in và chưa check-out, nhưng meeting kết thúc trong window.
        """
        from sqlalchemy.orm import aliased

        ParticipantAlias = aliased(ORMParticipant)

        stmt = (
            select(func.count(func.distinct(ParticipantAlias.user_id)))
            .join(ORMMeeting, ParticipantAlias.meeting_id == ORMMeeting.id)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ParticipantAlias.is_deleted.is_(False),
                ParticipantAlias.check_in_at.is_not(None),
                ParticipantAlias.check_out_at.is_(None),
                ORMMeeting.end_time > now,
                ORMMeeting.end_time <= window_end,
            )
        )
        result = self.session.scalars(stmt).first()
        return result or 0


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
            check_out_at=orm.check_out_at,
            link_image=orm.link_image,
            user=user_ref,
        )

    def find_participation_in_time_window(
        self,
        user_id: int,
        window_start: datetime,
        window_end: datetime,
        now: datetime,
    ) -> DomainParticipant | None:
        """Participant của user trong meeting giao [window_start, window_end] với khung họp."""
        ongoing_expr = and_(
            ORMMeeting.start_time <= now,
            ORMMeeting.end_time >= now,
        )
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, ORMMeeting.id == ORMParticipant.meeting_id)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMParticipant.is_deleted.is_(False),
                ORMParticipant.user_id == user_id,
                ORMMeeting.start_time < window_end,
                ORMMeeting.end_time > window_start,
            )
            .options(
                joinedload(ORMParticipant.user),
                joinedload(ORMParticipant.meeting),
            )
            .order_by(case({ongoing_expr: 0}, else_=1), desc(ORMMeeting.start_time))
            .limit(1)
        )
        orm = self.session.scalars(stmt).first()
        return self._to_domain(orm) if orm else None

    def find_all_participations_in_time_window(
        self,
        user_id: int,
        window_start: datetime,
        window_end: datetime,
        now: datetime,
    ) -> list[DomainParticipant]:
        """Lấy tất cả các buổi họp của user giao với [window_start, window_end]."""
        ongoing_expr = and_(
            ORMMeeting.start_time <= now,
            ORMMeeting.end_time >= now,
        )
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, ORMMeeting.id == ORMParticipant.meeting_id)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMParticipant.is_deleted.is_(False),
                ORMParticipant.user_id == user_id,
                ORMMeeting.start_time < window_end,
                ORMMeeting.end_time > window_start,
            )
            .options(
                joinedload(ORMParticipant.user),
                joinedload(ORMParticipant.meeting),
            )
            .order_by(case({ongoing_expr: 0}, else_=1), desc(ORMMeeting.start_time))
        )
        orms = self.session.scalars(stmt).all()
        return [self._to_domain(orm) for orm in orms]

    def get_by_meeting_and_user(
        self, meeting_id: int, user_id: int
    ) -> DomainParticipant | None:
        stmt = select(ORMParticipant).where(
            and_(
                ORMParticipant.user_id == user_id,
                ORMParticipant.meeting_id == meeting_id,
                ORMParticipant.is_deleted == False,  # noqa: E712
            )
        )
        orm = self.session.scalars(stmt).first()
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
        orm.check_out_at = domain.check_out_at
        orm.link_image = domain.link_image

        self.session.add(orm)
        self.session.flush()
        domain.id = orm.id
        return domain

    def check_out(
        self, participant_id: int, check_out_time: datetime
    ) -> DomainParticipant:
        """Cập nhật check-out cho participant."""
        orm = self.session.get(ORMParticipant, participant_id)
        if not orm:
            raise ValueError("Participant not found")

        orm.check_out_at = check_out_time
        orm.status = ParticipantStatus.COMPLETED
        self.session.add(orm)
        self.session.flush()
        return self._to_domain(orm)

    def get_completed_since(self, since: datetime) -> list[DomainParticipant]:
        """Lấy participants đã check-out sau thời điểm since."""
        stmt = (
            select(ORMParticipant)
            .where(
                ORMParticipant.is_deleted.is_(False),
                ORMParticipant.check_out_at.is_not(None),
                ORMParticipant.check_out_at >= since,
            )
            .options(joinedload(ORMParticipant.user))
        )
        orms = self.session.scalars(stmt).all()
        return [self._to_domain(orm) for orm in orms]

    def delete_by_meeting(self, meeting_id: int) -> bool:
        statement = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id
        )
        orms = self.session.scalars(statement).all()
        for orm in orms:
            orm.is_deleted = True
            self.session.add(orm)
        return True
