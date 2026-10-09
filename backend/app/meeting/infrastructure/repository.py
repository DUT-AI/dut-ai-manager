from datetime import date, datetime
from typing import Any, cast

from sqlalchemy import and_, case, desc, extract, func, or_, select
from sqlalchemy.orm import Session, contains_eager, joinedload, selectinload

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import (
    FilterCriterion,
    FilterOperator,
    QuerySupport,
    apply_query_support,
)
from app.shared.infrastructure.base_repository import BaseRepository

from ..domain.entity import Meeting as DomainMeeting
from ..domain.entity import MeetingEvaluation as DomainEvaluation
from ..domain.entity import MeetingParticipant as DomainParticipant
from ..domain.value_objects import ParticipantStatus
from .model import Meeting as ORMMeeting
from .model import MeetingEvaluation as ORMEvaluation
from .model import MeetingParticipant as ORMParticipant


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
        """Lấy Meeting và khóa dòng (Pessimistic Lock with_for_update) chống race condition."""
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
        """Lấy danh sách các buổi họp sắp tới từ mốc start_threshold, sắp xếp theo start_time tăng dần."""
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

    def get_all_with_participants(
        self,
        query_support: QuerySupport | None = None,
        deleted: bool = False,
        skip: int = 0,
        limit: int = 100,
        month: int | None = None,
        year: int | None = None,
    ) -> list[DomainMeeting]:

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
        orm.enable_evaluation = domain.enable_evaluation
        orm.evaluation_deadline = domain.evaluation_deadline

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

        # Commit is handled by middleware, but we need to refresh to get updated participants for the return
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
        return orm.to_entity()

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

    def update_participant_status(
        self,
        meeting_id: int,
        user_id: int,
        status: ParticipantStatus,
        check_in_at: datetime | None = None,
        check_out_at: datetime | None = None,
    ) -> DomainParticipant:
        """Cập nhật thủ công trạng thái và thời gian checkin/checkout cho participant."""
        stmt = (
            select(ORMParticipant)
            .where(
                ORMParticipant.meeting_id == meeting_id,
                ORMParticipant.user_id == user_id,
                ORMParticipant.is_deleted.is_(False),
            )
            .options(joinedload(ORMParticipant.user))
        )
        orm = self.session.scalars(stmt).first()
        if not orm:
            raise ValueError(
                f"Không tìm thấy tham gia của user {user_id} trong meeting {meeting_id}"
            )

        orm.status = status
        orm.check_in_at = check_in_at
        orm.check_out_at = check_out_at
        if status == ParticipantStatus.NOT_JOINED:
            orm.link_image = None

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

    def get_by_user_and_month(
        self, user_id: int, month: int, year: int
    ) -> list[DomainParticipant]:
        """Lấy tất cả session đã check-in của user trong tháng."""
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, ORMParticipant.meeting_id == ORMMeeting.id)
            .where(
                ORMParticipant.is_deleted.is_(False),
                ORMParticipant.user_id == user_id,
                ORMParticipant.check_in_at.is_not(None),
                extract("month", ORMMeeting.start_time) == month,
                extract("year", ORMMeeting.start_time) == year,
            )
            .order_by(ORMMeeting.start_time.asc())
            .options(joinedload(ORMParticipant.user))
        )
        return [self._to_domain(orm) for orm in self.session.scalars(stmt).all()]


class MeetingEvaluationRepository(BaseRepository[ORMEvaluation, DomainEvaluation]):
    """Repository quản lý các phiếu đánh giá 2 chiều (MeetingEvaluation)"""

    def __init__(self, session: Session):
        super().__init__(session, ORMEvaluation)

    def _to_domain(self, orm: ORMEvaluation) -> DomainEvaluation:
        return orm.to_entity()

    def save(self, entity: DomainEvaluation) -> DomainEvaluation:
        """Lưu hoặc cập nhật phiếu đánh giá (MeetingEvaluation)."""
        if entity.id:
            orm = self.session.get(ORMEvaluation, entity.id)
            if not orm:
                orm = ORMEvaluation.from_entity(entity)
            else:
                orm.scores = [s.model_dump() for s in entity.scores]
                orm.average_score = entity.average_score
                orm.feedback_text = entity.feedback_text
                orm.is_anonymous = entity.is_anonymous
        else:
            orm = ORMEvaluation.from_entity(entity)

        self.session.add(orm)
        self.session.flush()
        return orm.to_entity()

    def get_by_meeting_and_users(
        self, meeting_id: int, reviewer_id: int, target_user_id: int
    ) -> DomainEvaluation | None:
        stmt = (
            select(ORMEvaluation)
            .where(
                ORMEvaluation.meeting_id == meeting_id,
                ORMEvaluation.reviewer_id == reviewer_id,
                ORMEvaluation.target_user_id == target_user_id,
                ORMEvaluation.is_deleted.is_(False),
            )
            .options(
                joinedload(ORMEvaluation.reviewer),
                joinedload(ORMEvaluation.target_user),
            )
        )
        orm = self.session.scalars(stmt).first()
        return self._to_domain(orm) if orm else None

    def get_evaluations_by_meeting(
        self, meeting_id: int, evaluation_type: str | None = None
    ) -> list[DomainEvaluation]:
        stmt = (
            select(ORMEvaluation)
            .where(
                ORMEvaluation.meeting_id == meeting_id,
                ORMEvaluation.is_deleted.is_(False),
            )
            .options(
                joinedload(ORMEvaluation.reviewer),
                joinedload(ORMEvaluation.target_user),
            )
            .order_by(desc(ORMEvaluation.created_at))
        )
        if evaluation_type:
            stmt = stmt.where(ORMEvaluation.evaluation_type == evaluation_type)
        orms = self.session.scalars(stmt).all()
        return [self._to_domain(orm) for orm in orms]

    def get_evaluations_for_user_in_meeting(
        self, meeting_id: int, target_user_id: int
    ) -> list[DomainEvaluation]:
        stmt = (
            select(ORMEvaluation)
            .where(
                ORMEvaluation.meeting_id == meeting_id,
                ORMEvaluation.target_user_id == target_user_id,
                ORMEvaluation.is_deleted.is_(False),
            )
            .options(
                joinedload(ORMEvaluation.reviewer),
                joinedload(ORMEvaluation.target_user),
            )
        )
        orms = self.session.scalars(stmt).all()
        return [self._to_domain(orm) for orm in orms]

    def count_evaluations_by_reviewer(self, meeting_id: int, reviewer_id: int) -> int:
        stmt = select(func.count(ORMEvaluation.id)).where(
            ORMEvaluation.meeting_id == meeting_id,
            ORMEvaluation.reviewer_id == reviewer_id,
            ORMEvaluation.is_deleted.is_(False),
        )
        return self.session.scalar(stmt) or 0
