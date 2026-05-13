from loguru import logger

from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.meeting.domain.events import MeetingAbsenceDetected, ParticipantCheckedIn
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.application.event_handler import EventHandler
from app.utils.datetime import get_current_utc7_time
from app.violation.application.use_cases import CreateViolationUseCase


class AutomatedViolationHandler(EventHandler):
    """Xử lý các sự kiện vi phạm được phát hiện tự động."""

    def __init__(
        self,
        create_violation_use_case: CreateViolationUseCase,
        permission_repo: PermissionRequestRepository,
    ):
        self.create_violation_use_case = create_violation_use_case
        self.permission_repo = permission_repo

    async def handle(self, event):
        """Điều hướng sự kiện đến phương thức xử lý tương ứng."""
        if isinstance(event, HomeworkOverdueDetected):
            await self._handle_homework_overdue(event)
        elif isinstance(event, MeetingAbsenceDetected):
            await self._handle_meeting_absence(event)
        elif isinstance(event, ParticipantCheckedIn):
            await self._handle_meeting_late(event)

    async def _handle_homework_overdue(self, event: HomeworkOverdueDetected):
        """Tạo vi phạm khi quá hạn bài tập."""
        now = get_current_utc7_time()
        await self.create_violation_use_case.execute(
            user_ids=[event.user_id],
            reason=f"{event.reason}: {event.homework_title}",
            date=now,
            is_system=True,
            system_user_id=None,
        )

    async def _handle_meeting_absence(self, event: MeetingAbsenceDetected):
        """Tạo vi phạm khi vắng họp (có kiểm tra đơn xin phép)."""
        now = get_current_utc7_time()

        await self.create_violation_use_case.execute(
            user_ids=[event.user_id],
            reason=f"Vắng sinh hoạt: {event.meeting_title} (Không có giấy xin phép)",
            date=now,
            is_system=True,
            system_user_id=None,
        )

    async def _handle_meeting_late(self, event: ParticipantCheckedIn):
        """Tạo vi phạm khi đi trễ sinh hoạt (có kiểm tra đơn xin phép)."""
        logger.debug(f"Handling ParticipantCheckedIn: {event}")
        if event.is_late:
            now = get_current_utc7_time()

            # Kiểm tra xem người dùng có đơn xin đi trễ không
            requests = self.permission_repo.get_by_user(
                user_id=event.user_id, month=now.month, year=now.year
            )

            late_request = None
            for req in requests:
                if (
                    req.category == RequestCategory.LATE
                    and req.meeting_id == event.meeting_id
                ):
                    late_request = req
                    break

            reason = f"Đi trễ sinh hoạt: {event.meeting_title}"

            if late_request:
                # Nếu có xin phép, kiểm tra xem có đi trễ hơn thời gian xin phép không
                if (
                    late_request.start_time
                    and event.check_in_at <= late_request.start_time
                ):
                    logger.info(
                        f"User {event.user_id} check-in within permission window. Skipping violation."
                    )
                    return
                else:
                    # Đi trễ hơn thời gian xin phép
                    limit_str = (
                        late_request.start_time.strftime("%H:%M")
                        if late_request.start_time
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
