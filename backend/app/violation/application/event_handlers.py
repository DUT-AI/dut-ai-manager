from datetime import datetime
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
from app.utils.datetime import get_current_utc7_time
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
        now = get_current_utc7_time()
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
        if self.participant_repo:
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
        now = get_current_utc7_time()
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
            if self.participant_repo:
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
            limit_time = (
                late_req.start_time.replace(tzinfo=None)
                if late_req.start_time.tzinfo is not None
                else late_req.start_time
            )
            check_in_time = (
                event.check_in_at.replace(tzinfo=None)
                if event.check_in_at.tzinfo is not None
                else event.check_in_at
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
            if self.participant_repo:
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
            reason = f"Đi trễ hơn thời gian xin phép ({limit_str}): {event.meeting_title}"
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
        """Xử lý bài tập quá hạn: kiểm tra đơn xin hoãn (POSTPONE) và tạo vi phạm nếu không hợp lệ."""
        now = get_current_utc7_time()
        logger.info(
            f"🔍 [ViolationHandler] Processing overdue homework for user {event.user_id} in homework {event.homework_id}"
        )

        postpone_requests = self.permission_repo.get_postpone_requests_for_homeworks(
            homework_ids=[event.homework_id], user_ids=[event.user_id]
        )
        postpone_req = next(iter(postpone_requests), None)

        now_naive = now.replace(tzinfo=None)
        has_valid_postpone = False
        if postpone_req and postpone_req.start_time:
            req_time = (
                postpone_req.start_time.replace(tzinfo=None)
                if postpone_req.start_time.tzinfo is not None
                else postpone_req.start_time
            )
            if now_naive <= req_time:
                has_valid_postpone = True

        if has_valid_postpone:
            logger.info(
                f"✅ [ViolationHandler] User {event.user_id} có đơn xin hoãn bài tập '{event.homework_title}' hợp lệ."
            )
            return

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
