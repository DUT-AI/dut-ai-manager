from datetime import date

from sqlalchemy import desc, extract, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.model import (
    MeetingParticipant as ORMParticipant,
)
from app.permission_request.domain.entity import PermissionRequest as DomainEntity
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.model import PermissionRequest as ORMModel
from app.shared.domain.query_support import (
    QuerySupport,
    apply_filters_only,
    apply_query_support,
)
from app.shared.infrastructure.base_repository import BaseRepository


class PermissionRequestRepository(BaseRepository[ORMModel, DomainEntity]):
    """ORM-first (kế thừa BaseRepository); public API trả domain entity."""

    def __init__(self, session: Session):
        super().__init__(session, ORMModel)

    def get_paged(
        self, query_support: QuerySupport | None = None, deleted: bool = False
    ) -> tuple[list[DomainEntity], int]:
        """Get paginated permission requests with eager-loaded relations."""

        count_stmt = select(func.count(ORMModel.id)).where(
            ORMModel.is_deleted == deleted
        )
        data_stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.creator),
            )
            .where(ORMModel.is_deleted == deleted)
        )

        if query_support:
            count_stmt = apply_filters_only(count_stmt, ORMModel, query_support.filters)
            data_stmt = apply_query_support(data_stmt, ORMModel, query_support)
            if not query_support.sorting:
                sort_field = ORMModel.updated_at if deleted else ORMModel.created_at
                data_stmt = data_stmt.order_by(sort_field.desc(), ORMModel.id.desc())
        else:
            sort_field = ORMModel.updated_at if deleted else ORMModel.created_at
            data_stmt = data_stmt.order_by(sort_field.desc(), ORMModel.id.desc())

        total = self.session.scalar(count_stmt) or 0
        rows = self.session.scalars(data_stmt).unique().all()
        return [r.to_entity() for r in rows], total

    def get_by_date(self, target_date: date) -> list[DomainEntity]:
        """Lấy tất cả yêu cầu xin phép trong một ngày cụ thể."""
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.creator),
            )
            .where(
                ORMModel.is_deleted.is_(False),
                func.date(ORMModel.created_at) == target_date,
            )
            .order_by(desc(ORMModel.created_at))
        )
        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_by_month(
        self,
        month: int,
        year: int,
        limit: int = 1000,
        deleted: bool = False,
    ) -> list[DomainEntity]:
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.creator),
            )
            .where(
                ORMModel.is_deleted == deleted,
                extract("month", ORMModel.created_at) == month,
                extract("year", ORMModel.created_at) == year,
            )
            .order_by(desc(ORMModel.created_at))
            .limit(limit)
        )
        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_by_user(
        self,
        user_id: int,
        month: int | None = None,
        year: int | None = None,
        deleted: bool = False,
    ) -> list[DomainEntity]:
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.creator),
            )
            .where(
                ORMModel.created_by == user_id,
                ORMModel.is_deleted == deleted,
            )
        )

        if month is not None:
            stmt = stmt.where(extract("month", ORMModel.created_at) == month)
        if year is not None:
            stmt = stmt.where(extract("year", ORMModel.created_at) == year)

        stmt = stmt.order_by(desc(ORMModel.created_at))
        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_detail_by_id(self, request_id: int) -> ORMModel | None:
        """Lấy chi tiết đơn xin phép kèm theo liên kết User creator/updater."""
        stmt = (
            select(ORMModel)
            .options(
                joinedload(ORMModel.creator),
                joinedload(ORMModel.updater),
            )
            .where(ORMModel.id == request_id, ORMModel.is_deleted.is_(False))
        )
        return self.session.scalars(stmt).unique().first()

    def get_requests_for_meetings(
        self, meeting_ids: list[int], user_ids: list[int]
    ) -> list[DomainEntity]:
        """Lấy tất cả đơn xin phép liên quan đến danh sách meeting_id hoặc user_id."""
        if not user_ids:
            return []

        stmt = select(ORMModel).where(
            ORMModel.is_deleted == False,  # noqa: E712
            ORMModel.created_by.in_(user_ids),
        )
        if meeting_ids:
            stmt = stmt.where(
                or_(
                    ORMModel.payload["meeting_id"].as_integer().in_(meeting_ids),
                    ORMModel.payload["meeting_id"].as_integer().is_(None),
                )
            )

        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_postpone_requests_for_homeworks(
        self, homework_ids: list[int], user_ids: list[int]
    ) -> list[DomainEntity]:
        """Lấy danh sách đơn xin hoãn cho các bài tập và user cụ thể."""
        if not homework_ids or not user_ids:
            return []

        stmt = select(ORMModel).where(
            ORMModel.payload["homework_id"].as_integer().in_(homework_ids),
            ORMModel.created_by.in_(user_ids),
            ORMModel.category == RequestCategory.POSTPONE,
            ORMModel.is_deleted.is_(False),
        )

        rows = self.session.scalars(stmt).unique().all()
        return [r.to_entity() for r in rows]

    def get_absence_user_ids_by_meeting(self, meeting_id: int) -> set[int]:
        """Lấy danh sách user_id có đơn xin vắng (ABSENCE) của một meeting."""
        stmt = select(ORMModel.created_by).where(
            ORMModel.payload["meeting_id"].as_integer() == meeting_id,
            ORMModel.category == RequestCategory.ABSENCE,
            ORMModel.is_deleted.is_(False),
        )
        rows = self.session.scalars(stmt).all()
        return {r for r in rows if r is not None}

    def get_transferred_out_user_ids_by_meeting(self, meeting_id: int) -> set[int]:
        """Lấy user_id có đơn chuyển ĐI khỏi meeting (old_meeting_id == meeting_id)."""
        stmt = select(ORMModel.created_by).where(
            ORMModel.payload["old_meeting_id"].as_integer() == meeting_id,
            ORMModel.category == RequestCategory.CHANGE_MEETING,
            ORMModel.is_deleted.is_(False),
        )
        rows = self.session.scalars(stmt).all()
        return {r for r in rows if r is not None}

    def get_transferred_in_user_ids_by_meeting(self, meeting_id: int) -> set[int]:
        """Lấy user_id có đơn chuyển ĐẾN meeting (meeting_id == meeting_id)."""
        stmt = select(ORMModel.created_by).where(
            ORMModel.payload["meeting_id"].as_integer() == meeting_id,
            ORMModel.category == RequestCategory.CHANGE_MEETING,
            ORMModel.is_deleted.is_(False),
        )
        rows = self.session.scalars(stmt).all()
        return {r for r in rows if r is not None}

    def get_all_excused_or_transferred_out_user_ids(
        self, meeting_id: int
    ) -> set[int]:
        """Lấy user_id không tham gia: vắng (ABSENCE) hoặc chuyển ca."""
        return self.get_absence_user_ids_by_meeting(
            meeting_id
        ) | self.get_transferred_out_user_ids_by_meeting(meeting_id)

    def mark_participant_excused(self, meeting_id: int, user_id: int) -> None:
        """Đánh dấu participant trong meeting_participants thành ABSENT_EXCUSED."""

        stmt = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id,
            ORMParticipant.user_id == user_id,
            ORMParticipant.is_deleted.is_(False),
        )
        p = self.session.scalars(stmt).first()
        if p:
            p.status = ParticipantStatus.ABSENT_EXCUSED
            self.session.flush()

    def mark_participant_late_excused(self, meeting_id: int, user_id: int) -> None:
        """Đánh dấu participant thành LATE_EXCUSED nếu chưa check-in."""
        stmt = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id,
            ORMParticipant.user_id == user_id,
            ORMParticipant.is_deleted.is_(False),
        )
        p = self.session.scalars(stmt).first()
        if p and p.status == ParticipantStatus.NOT_JOINED:
            p.status = ParticipantStatus.LATE_EXCUSED
            self.session.flush()

    def revert_participant_excused(self, meeting_id: int, user_id: int) -> None:
        """Khôi phục participant về NOT_JOINED nếu không còn đơn vắng/trễ."""
        stmt = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id,
            ORMParticipant.user_id == user_id,
            ORMParticipant.is_deleted.is_(False),
        )
        p = self.session.scalars(stmt).first()
        if p and p.status in (
            ParticipantStatus.ABSENT_EXCUSED,
            ParticipantStatus.LATE_EXCUSED,
        ):
            p.status = ParticipantStatus.NOT_JOINED
            self.session.flush()

    def cancel_active_requests_by_meeting(self, user_id: int, meeting_id: int) -> int:
        """Hủy mềm (is_deleted = True) các đơn xin vắng/trễ của user tại meeting_id."""
        stmt = select(ORMModel).where(
            ORMModel.created_by == user_id,
            ORMModel.payload["meeting_id"].as_integer() == meeting_id,
            ORMModel.category.in_([RequestCategory.ABSENCE, RequestCategory.LATE]),
            ORMModel.is_deleted.is_(False),
        )
        rows = self.session.scalars(stmt).all()
        count = 0
        for r in rows:
            r.is_deleted = True
            count += 1
        if count > 0:
            self.session.flush()
        return count

    def update(self, entity: DomainEntity) -> DomainEntity:
        return super().update(entity)

    def save(self, entity: DomainEntity) -> DomainEntity:
        if entity.id:
            return self.update(entity)
        return self.add(entity)

    def delete(self, request_id: int) -> bool:
        entity = self.get_by_id(request_id)
        if entity:
            self.soft_delete(entity)
            return True
        return False
