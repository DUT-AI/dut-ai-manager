from datetime import datetime

from sqlalchemy import and_, case, desc, extract, select
from sqlalchemy.orm import Session, joinedload

from app.meeting.domain.participant import MeetingParticipant as DomainParticipant
from app.meeting.domain.value_objects import ParticipantRole, ParticipantStatus
from app.meeting.infrastructure.model import Meeting as ORMMeeting
from app.meeting.infrastructure.model import MeetingParticipant as ORMParticipant
from app.shared.infrastructure.base_repository import BaseRepository


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
        """Participant của user giao [window_start, window_end] với khung họp."""
        ongoing_expr = and_(
            ORMMeeting.start_time <= now,
            ORMMeeting.end_time >= now,
        )
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, ORMMeeting.id == ORMParticipant.meeting_id)
            .where(
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
        orm.client_event_id = domain.client_event_id

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
        """Cập nhật trạng thái và thời gian checkin/checkout cho participant."""
        stmt = (
            select(ORMParticipant)
            .where(
                ORMParticipant.meeting_id == meeting_id,
                ORMParticipant.user_id == user_id,
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
            self.session.delete(orm)
        return True

    def remove_participant(self, meeting_id: int, user_id: int) -> bool:
        """Xóa trực tiếp (hard delete) bản ghi participant khỏi buổi họp."""
        stmt = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id,
            ORMParticipant.user_id == user_id,
        )
        orm = self.session.scalars(stmt).first()
        if not orm:
            return False
        self.session.delete(orm)
        self.session.flush()
        return True

    def add_participant(self, domain: DomainParticipant) -> DomainParticipant:
        """Thêm mới hoặc cập nhật/kích hoạt lại participant trong buổi họp."""
        stmt = select(ORMParticipant).where(
            ORMParticipant.meeting_id == domain.meeting_id,
            ORMParticipant.user_id == domain.user_id,
        )
        orm = self.session.scalars(stmt).first()
        role_val = (
            domain.role.value
            if isinstance(domain.role, ParticipantRole)
            else (domain.role or ParticipantRole.TRAINEE.value)
        )
        if not orm:
            orm = ORMParticipant(
                meeting_id=domain.meeting_id,
                user_id=domain.user_id,
                role=role_val,
                status=domain.status or ParticipantStatus.NOT_JOINED,
                check_in_at=domain.check_in_at,
                check_out_at=domain.check_out_at,
                link_image=domain.link_image,
                client_event_id=domain.client_event_id,
            )
            self.session.add(orm)
        else:
            orm.role = role_val
            orm.status = domain.status or ParticipantStatus.NOT_JOINED
            orm.check_in_at = domain.check_in_at
            orm.check_out_at = domain.check_out_at
            orm.link_image = domain.link_image
            orm.client_event_id = domain.client_event_id
            self.session.add(orm)
        self.session.flush()
        return self._to_domain(orm)

    def bulk_create(
        self, meeting_id: int, participants: list[DomainParticipant]
    ) -> list[DomainParticipant]:
        """Tạo danh sách participants ban đầu khi tạo meeting mới."""
        created_orms: list[ORMParticipant] = []
        for dp in participants:
            role_val = (
                dp.role.value
                if isinstance(dp.role, ParticipantRole)
                else (dp.role or ParticipantRole.TRAINEE.value)
            )
            po = ORMParticipant(
                meeting_id=meeting_id,
                user_id=dp.user_id,
                role=role_val,
                status=dp.status or ParticipantStatus.NOT_JOINED,
                check_in_at=dp.check_in_at,
                check_out_at=dp.check_out_at,
                link_image=dp.link_image,
                client_event_id=dp.client_event_id,
            )
            self.session.add(po)
            created_orms.append(po)
        self.session.flush()
        return [self._to_domain(po) for po in created_orms]

    def sync_meeting_participants(
        self,
        meeting_id: int,
        new_trainers: set[int],
        new_trainees: set[int],
    ) -> None:
        """Đồng bộ danh sách Trainer và Trainee của meeting theo set user_id."""
        stmt = select(ORMParticipant).where(
            ORMParticipant.meeting_id == meeting_id,
        )
        existing_participants = self.session.scalars(stmt).all()
        existing_map = {p.user_id: p for p in existing_participants}

        all_target_user_ids = new_trainers | new_trainees

        # 1. Hard delete các participant không còn trong danh sách mới
        for old_user_id, old_p in existing_map.items():
            if old_user_id not in all_target_user_ids:
                self.session.delete(old_p)

        # 2. Cập nhật hoặc thêm mới Trainer
        for uid in new_trainers:
            if uid in existing_map:
                existing = existing_map[uid]
                existing.role = ParticipantRole.TRAINER.value
                self.session.add(existing)
            else:
                po = ORMParticipant(
                    meeting_id=meeting_id,
                    user_id=uid,
                    role=ParticipantRole.TRAINER.value,
                    status=ParticipantStatus.NOT_JOINED,
                )
                self.session.add(po)

        # 3. Cập nhật hoặc thêm mới Trainee
        for uid in new_trainees:
            if uid in existing_map:
                existing = existing_map[uid]
                existing.role = ParticipantRole.TRAINEE.value
                self.session.add(existing)
            else:
                po = ORMParticipant(
                    meeting_id=meeting_id,
                    user_id=uid,
                    role=ParticipantRole.TRAINEE.value,
                    status=ParticipantStatus.NOT_JOINED,
                )
                self.session.add(po)

        self.session.flush()

    def get_by_user_and_month(
        self, user_id: int, month: int, year: int
    ) -> list[DomainParticipant]:
        """Lấy tất cả session đã check-in của user trong tháng."""
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, ORMParticipant.meeting_id == ORMMeeting.id)
            .where(
                ORMParticipant.user_id == user_id,
                ORMParticipant.check_in_at.is_not(None),
                extract("month", ORMMeeting.start_time) == month,
                extract("year", ORMMeeting.start_time) == year,
            )
            .order_by(ORMMeeting.start_time.asc())
            .options(joinedload(ORMParticipant.user))
        )
        return [self._to_domain(orm) for orm in self.session.scalars(stmt).all()]

    def get_all_by_month(self, month: int, year: int) -> list[DomainParticipant]:
        """Lấy tất cả session đã check-in của user trong tháng."""
        stmt = (
            select(ORMParticipant)
            .join(ORMMeeting, ORMParticipant.meeting_id == ORMMeeting.id)
            .where(
                ORMParticipant.check_in_at.is_not(None),
                extract("month", ORMMeeting.start_time) == month,
                extract("year", ORMMeeting.start_time) == year,
            )
            .order_by(ORMMeeting.start_time.asc())
            .options(joinedload(ORMParticipant.user))
        )
        return [self._to_domain(orm) for orm in self.session.scalars(stmt).all()]


__all__ = ["ParticipantRepository"]
