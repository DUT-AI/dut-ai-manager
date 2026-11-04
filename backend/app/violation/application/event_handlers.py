from datetime import UTC, datetime

from loguru import logger

from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.meeting.domain.events import (
    MeetingAbsenceDetected,
    ParticipantAbsenceRecorded,
    ParticipantLateRecorded,
)
from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import ParticipantRepository
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.application.event_handler import EventHandler
from app.violation.application.create_violation_use_case import CreateViolationUseCase


class AutomatedViolationHandler(EventHandler):
    """
    Xử lý các sự kiện vi phạm và quyết định kỷ luật tập trung.
    Lắng nghe sự kiện từ Meeting và Homework, tra cứu đơn xin phép và quyết định tạo vi phạm.
    """

    def __init__(
        self,
        create_violation_use_case: CreateViolationUseCase,
        permission_repo: PermissionRequestRepository,
        participant_repo: ParticipantRepository,
    ):
        self.create_violation_use_case = create_violation_use_case
        self.permission_repo = permission_repo
        self.participant_repo = participant_repo

    async def handle(self, event):
        """Điều hướng sự kiện đến phương thức xử lý tương ứng."""
        if isinstance(event, (ParticipantAbsenceRecorded, MeetingAbsenceDetected)):
            await self._handle_meeting_absence(event)
        elif isinstance(event, ParticipantLateRecorded):
            await self._handle_meeting_late(event)
        elif isinstance(event, HomeworkOverdueDetected):
            await self._handle_homework_overdue(event)

    async def _handle_meeting_absence(
        self, event: ParticipantAbsenceRecorded | MeetingAbsenceDetected
    ):
        """Xử lý vắng họp: tra cứu đơn xin vắng, cập nhật trạng thái và tạo vi phạm nếu không phép."""
        now = datetime.now(UTC)
        logger.info(
            f"🔍 [ViolationHandler] Processing absence for user {event.user_id} in meeting {event.meeting_id}"
        )

        requests = self.permission_repo.get_requests_for_meetings(
            [event.meeting_id], [event.user_id]
        )
        absence_req = next(
            (r for r in requests if r.category == RequestCategory.ABSENCE), None
        )

        if absence_req:
            logger.info(
                f"✅ [ViolationHandler] User {event.user_id} vắng có phép tại '{event.meeting_title}'"
            )
            try:
                self.participant_repo.update_participant_status(
                    meeting_id=event.meeting_id,
                    user_id=event.user_id,
                    status=ParticipantStatus.ABSENT_EXCUSED,
                )
            except Exception as e:
                logger.warning(f"Could not update participant status: {e}")
            return

        # Vắng không phép -> Tạo vi phạm
        try:
            self.participant_repo.update_participant_status(
                meeting_id=event.meeting_id,
                user_id=event.user_id,
                status=ParticipantStatus.ABSENT_UNEXCUSED,
            )
        except Exception as e:
            logger.warning(
                f"Could not update participant status for user {event.user_id} in meeting {event.meeting_id}: {e}. Skipping violation creation."
            )
            return

        reason = f"Vắng sinh hoạt: {event.meeting_title} (Không xin phép)"
        await self.create_violation_use_case.execute(
            user_ids=[event.user_id],
            reason=reason,
            date=now,
            is_system=True,
            system_user_id=None,
        )
        logger.info(
            f"🚨 [ViolationHandler] Created absence violation for user {event.user_id}"
        )

    async def _handle_meeting_late(self, event: ParticipantLateRecorded):
        """Xử lý đi trễ: tra cứu đơn xin trễ, đối soát thời gian và tạo vi phạm nếu trễ không phép."""
        now = datetime.now(UTC)
        logger.info(
            f"🔍 [ViolationHandler] Processing late arrival for user {event.user_id} in meeting {event.meeting_id}"
        )

        requests = self.permission_repo.get_requests_for_meetings(
            [event.meeting_id], [event.user_id]
        )
        late_req = next(
            (r for r in requests if r.category == RequestCategory.LATE), None
        )

        if late_req is None:
            try:
                self.participant_repo.update_participant_status(
                    meeting_id=event.meeting_id,
                    user_id=event.user_id,
                    status=ParticipantStatus.LATE_UNEXCUSED,
                )
            except Exception as e:
                logger.warning(
                    f"Could not update participant status for user {event.user_id} in meeting {event.meeting_id}: {e}. Skipping violation creation."
                )
                return

            reason = f"Đi trễ sinh hoạt: {event.meeting_title} (Không xin phép)"
            await self.create_violation_use_case.execute(
                user_ids=[event.user_id],
                reason=reason,
                date=now,
                is_system=True,
                system_user_id=None,
            )
            logger.info(
                f"🚨 [ViolationHandler] Created unexcused late violation for user {event.user_id}"
            )
            return

        # Có đơn xin đi trễ -> Kiểm tra thời gian
        is_within_limit = True
        if late_req.start_time:
            # Chuẩn hóa về UTC timezone-aware để so sánh chính xác
            limit_time = (
                late_req.start_time
                if late_req.start_time.tzinfo is not None
                else late_req.start_time.replace(tzinfo=UTC)
            )
            check_in_time = (
                event.check_in_at
                if event.check_in_at.tzinfo is not None
                else event.check_in_at.replace(tzinfo=UTC)
            )
            if check_in_time > limit_time:
                is_within_limit = False

        if is_within_limit:
            logger.info(
                f"✅ [ViolationHandler] User {event.user_id} đi trễ có phép tại '{event.meeting_title}'"
            )
            if self.participant_repo:
                try:
                    self.participant_repo.update_participant_status(
                        meeting_id=event.meeting_id,
                        user_id=event.user_id,
                        status=ParticipantStatus.LATE_EXCUSED,
                    )
                except Exception as e:
                    logger.warning(f"Could not update participant status: {e}")
        else:
            try:
                self.participant_repo.update_participant_status(
                    meeting_id=event.meeting_id,
                    user_id=event.user_id,
                    status=ParticipantStatus.LATE_UNEXCUSED,
                )
            except Exception as e:
                logger.warning(
                    f"Could not update participant status for user {event.user_id} in meeting {event.meeting_id}: {e}. Skipping violation creation."
                )
                return

            limit_str = (
                late_req.start_time.strftime("%H:%M")
                if late_req.start_time
                else "thời gian quy định"
            )
            reason = (
                f"Đi trễ hơn thời gian xin phép ({limit_str}): {event.meeting_title}"
            )
            await self.create_violation_use_case.execute(
                user_ids=[event.user_id],
                reason=reason,
                date=now,
                is_system=True,
                system_user_id=None,
            )
            logger.info(
                f"🚨 [ViolationHandler] Created exceeded late violation for user {event.user_id}"
            )

    async def _handle_homework_overdue(self, event: HomeworkOverdueDetected):
        """Xử lý bài tập quá hạn và tạo vi phạm."""
        now = datetime.now(UTC)
        logger.info(
            f"🔍 [ViolationHandler] Processing overdue homework for user {event.user_id} in homework {event.homework_id}"
        )
        reason_msg = event.reason or f"Quá hạn nộp bài tập: {event.homework_title}"
        await self.create_violation_use_case.execute(
            user_ids=[event.user_id],
            reason=reason_msg,
            date=now,
            is_system=True,
            system_user_id=None,
        )
        logger.info(
            f"🚨 [ViolationHandler] Created homework violation for user {event.user_id}"
        )
