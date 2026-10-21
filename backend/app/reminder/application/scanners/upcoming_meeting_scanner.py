"""
Upcoming Meeting Attendance Task Scanner.
Scans meetings starting in the future (within a 48h lookahead window),
calculates matching reminder stages, and identifies participants who should attend
and have not yet checked in, automatically excluding excused absences and completed attendees.
"""

from datetime import datetime, timedelta

from app.meeting.domain.value_objects import ParticipantStatus
from app.meeting.infrastructure.repository import MeetingRepository
from app.reminder.application.scanners.base_scanner import (
    BaseTaskScanner,
    ScannedCandidateTask,
    calculate_matching_stages,
)
from app.reminder.domain.entity import TaskType


class UpcomingMeetingTaskScanner(BaseTaskScanner):
    def __init__(self, meeting_repo: MeetingRepository):
        self.meeting_repo = meeting_repo

    def scan_pending_tasks(self, now: datetime) -> list[ScannedCandidateTask]:
        candidates: list[ScannedCandidateTask] = []

        # Cửa sổ quét: các buổi họp diễn ra từ thời điểm hiện tại tới 48 giờ tiếp theo
        two_days_later = now + timedelta(days=2)
        meetings = self.meeting_repo.get_all_with_participants(
            start_date=now,
            end_date=two_days_later,
            limit=100,
        )

        for meeting in meetings:
            if not meeting.id or meeting.is_finished(now):
                continue

            stages = calculate_matching_stages(meeting.start_time, now)
            if not stages:
                continue

            for p in meeting.participants:
                # 1. Bỏ qua nếu bản ghi thành viên bị xóa mềm
                if p.is_deleted:
                    continue

                # 2. Bỏ qua thành viên đã điểm danh hoặc đã hoàn thành
                if p.status in (
                    ParticipantStatus.JOINED,
                    ParticipantStatus.COMPLETED,
                ):
                    continue

                # 3. Bỏ qua thành viên đã được duyệt đơn xin vắng sinh hoạt (ABSENT_EXCUSED)
                if p.status == ParticipantStatus.ABSENT_EXCUSED:
                    continue

                # 4. Bỏ qua nếu có trạng thái trễ có phép nhưng thực tế đã check-in
                if (
                    p.status == ParticipantStatus.LATE_EXCUSED
                    and p.check_in_at is not None
                ):
                    continue

                candidates.append(
                    ScannedCandidateTask(
                        task_type=TaskType.MEETING,
                        task_id=meeting.id,
                        task_title=f"Cuộc họp: {meeting.title}",
                        user_id=p.user_id,
                        deadline=meeting.start_time,
                        action_url=f"/dashboard/meetings/{meeting.id}",
                        stages=stages,
                    )
                )

        return candidates
