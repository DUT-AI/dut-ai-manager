from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.meeting.domain.meeting import Meeting as DomainMeeting
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.model import Meeting as ORMMeeting
from app.meeting.infrastructure.model import MeetingParticipant as ORMParticipant
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import (
    FilterCriterion,
    FilterOperator,
    QuerySupport,
    apply_query_support,
)
from app.shared.infrastructure.base_repository import BaseRepository


class MeetingRepository(BaseRepository[ORMMeeting, DomainMeeting]):
    def __init__(self, session: Session):
        super().__init__(session, ORMMeeting)

    def _to_domain(self, orm: ORMMeeting) -> DomainMeeting:
        return orm.to_entity()

    def get_by_id(self, id: int) -> DomainMeeting | None:
        """Override get_by_id để luôn eager load participants và creator."""
        return self.get_with_participants(id)

    def get_with_participants(self, meeting_id: int) -> DomainMeeting | None:
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMMeeting.id == meeting_id,
            )
            .options(
                selectinload(ORMMeeting.participants).joinedload(ORMParticipant.user),
                joinedload(ORMMeeting.creator),
            )
        )
        orm = self.session.scalars(statement).first()
        return self._to_domain(orm) if orm else None

    def get_meeting_with_lock(self, meeting_id: int) -> DomainMeeting | None:
        """Lấy Meeting và khóa dòng (Pessimistic Lock) chống race condition."""
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMMeeting.id == meeting_id,
            )
            .with_for_update(of=ORMMeeting)
            .options(
                selectinload(ORMMeeting.participants).joinedload(ORMParticipant.user),
                selectinload(ORMMeeting.creator),
            )
        )
        orm = self.session.scalars(statement).first()
        return self._to_domain(orm) if orm else None

    def get_upcoming_meetings(
        self, start_threshold: datetime, limit: int = 50
    ) -> list[DomainMeeting]:
        """Lấy các buổi họp sắp tới từ start_threshold theo start_time tăng dần."""
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMMeeting.start_time >= start_threshold,
            )
            .order_by(ORMMeeting.start_time.asc())
            .limit(limit)
            .options(
                selectinload(ORMMeeting.participants).joinedload(ORMParticipant.user),
                joinedload(ORMMeeting.creator),
            )
        )
        orms = self.session.scalars(statement).all()
        return [self._to_domain(orm) for orm in orms]

    def get_meetings_for_evaluation_deadline_check(
        self, start_bound: datetime, end_bound: datetime
    ) -> list[DomainMeeting]:
        """Lấy các buổi học kết thúc trong [start_bound, end_bound] có bật đánh giá."""
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                ORMMeeting.enable_evaluation.is_(True),
                ORMMeeting.end_time >= start_bound,
                ORMMeeting.end_time <= end_bound,
            )
            .options(
                selectinload(ORMMeeting.participants).joinedload(ORMParticipant.user),
                joinedload(ORMMeeting.creator),
            )
        )
        orms = self.session.scalars(statement).all()
        return [self._to_domain(orm) for orm in orms]

    def get_all_with_participants(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
        month: int | None = None,
        year: int | None = None,
        start_date: Any | None = None,
        end_date: Any | None = None,
    ) -> list[DomainMeeting]:
        if not query_support:
            filters = []
            if start_date is not None:
                filters.append(
                    FilterCriterion(
                        field="start_time",
                        operator=FilterOperator.GTE,
                        value=start_date,
                    )
                )
            if end_date is not None:
                filters.append(
                    FilterCriterion(
                        field="start_time",
                        operator=FilterOperator.LTE,
                        value=end_date,
                    )
                )
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
            .outerjoin(
                ORMParticipant,
                and_(
                    ORMMeeting.id == ORMParticipant.meeting_id,
                    ORMParticipant.is_deleted.is_(False),
                ),
            )
            .options(
                contains_eager(ORMMeeting.participants).joinedload(ORMParticipant.user)
            )
        )
        orms = self.session.scalars(statement).unique().all()
        return [self._to_domain(orm) for orm in orms]

    def get_by_date_range(
        self, start_date: date, end_date: date
    ) -> list[DomainMeeting]:
        statement = (
            select(ORMMeeting)
            .where(
                ORMMeeting.is_deleted.is_(False),
                func.date(ORMMeeting.start_time) >= start_date,
                func.date(ORMMeeting.start_time) <= end_date,
            )
            .order_by(ORMMeeting.start_time.asc())
            .outerjoin(
                ORMParticipant,
                and_(
                    ORMMeeting.id == ORMParticipant.meeting_id,
                    ORMParticipant.is_deleted.is_(False),
                ),
            )
            .options(
                contains_eager(ORMMeeting.participants).joinedload(ORMParticipant.user)
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

    def save(self, domain: DomainMeeting) -> DomainMeeting:  # noqa: C901
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
        orm.enable_evaluation = domain.enable_evaluation
        orm.evaluation_deadline = domain.evaluation_deadline
        if domain.created_by is not None:
            orm.created_by = domain.created_by

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
            # Sync participants correctly with hard delete for removed participants
            stmt = select(ORMParticipant).where(
                ORMParticipant.meeting_id == orm.id,
            )
            existing_participants = self.session.scalars(stmt).all()

            existing_user_ids = {p.user_id: p for p in existing_participants}
            new_user_ids = {p.user_id: p for p in domain.participants}

            # 1. Hard delete participants not in the new list
            for old_user_id, old_p in existing_user_ids.items():
                if old_user_id not in new_user_ids:
                    self.session.delete(old_p)

            # 2. Add or update participants
            for new_user_id, new_p in new_user_ids.items():
                if new_user_id not in existing_user_ids:
                    po = ORMParticipant(
                        meeting_id=orm.id,
                        user_id=new_user_id,
                        status=new_p.status,
                        check_in_at=new_p.check_in_at,
                        check_out_at=new_p.check_out_at,
                        link_image=new_p.link_image,
                    )
                    self.session.add(po)
                else:
                    existing = existing_user_ids[new_user_id]
                    existing.is_deleted = False
                    existing.status = new_p.status
                    existing.check_in_at = new_p.check_in_at
                    existing.check_out_at = new_p.check_out_at
                    existing.link_image = new_p.link_image
                    self.session.add(existing)

            self.session.flush()

        # Commit handled by middleware; refresh to get updated participants for return
        self.session.refresh(orm)
        return self.get_with_participants(orm.id) or self._to_domain(orm)

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
        Chỉ tính những người check-in trong ngày hôm nay để tránh lỗi đọng dữ liệu cũ.
        Và chỉ tính những người có status là JOINED (chưa checkout).
        """
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)

        stmt = select(func.count(ORMParticipant.id)).where(
            ORMParticipant.is_deleted.is_(False),
            ORMParticipant.check_in_at.is_not(None),
            ORMParticipant.check_in_at >= start_of_day,
            ORMParticipant.status == ParticipantStatus.JOINED,
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
        Chỉ tính người đã check-in, chưa check-out, và meeting kết thúc trong window.
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


__all__ = ["MeetingRepository"]
