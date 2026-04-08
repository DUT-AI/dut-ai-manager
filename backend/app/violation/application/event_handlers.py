from app.homework.domain.value_objects import HomeworkOverdueDetected
from app.meeting.domain.events import MeetingAbsenceDetected
from app.violation.application.use_cases import CreateViolationUseCase
from app.utils.datetime import get_current_utc7_time
from app.shared.application.event_handler import EventHandler


class AutomatedViolationHandler(EventHandler):
    """Xử lý các sự kiện vi phạm được phát hiện tự động."""

    def __init__(self, create_violation_use_case: CreateViolationUseCase):
        self.create_violation_use_case = create_violation_use_case

    async def handle(self, event):
        """Điều hướng sự kiện đến phương thức xử lý tương ứng."""
        if isinstance(event, HomeworkOverdueDetected):
            await self._handle_homework_overdue(event)
        elif isinstance(event, MeetingAbsenceDetected):
            await self._handle_meeting_absence(event)

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
        """Tạo vi phạm khi vắng họp không phép."""
        now = get_current_utc7_time()
        await self.create_violation_use_case.execute(
            user_ids=[event.user_id],
            reason=f"Vắng sinh hoạt: {event.meeting_title}",
            date=now,
            is_system=True,
            system_user_id=None,
        )
