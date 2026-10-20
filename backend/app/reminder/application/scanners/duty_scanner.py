"""
Duty Task Scanner.
Scans today's cleaning duties that are still pending or rejected before 22:00.
"""

from datetime import datetime
from app.duty.domain.entity import DutyStatus
from app.duty.infrastructure.repository import DutyRepository
from app.reminder.application.scanners.base_scanner import (
    BaseTaskScanner,
    ScannedCandidateTask,
    calculate_matching_stages,
)
from app.reminder.domain.entity import TaskType
from app.team.infrastructure.repository import TeamRepository


class DutyTaskScanner(BaseTaskScanner):
    def __init__(
        self,
        duty_repo: DutyRepository,
        team_repo: TeamRepository,
    ):
        self.duty_repo = duty_repo
        self.team_repo = team_repo

    def scan_pending_tasks(self, now: datetime) -> list[ScannedCandidateTask]:
        candidates: list[ScannedCandidateTask] = []
        today_date = now.date()
        today_duties = self.duty_repo.get_pending_duties_for_date(today_date)

        for duty in today_duties:
            if not duty.id or duty.status not in (DutyStatus.PENDING, DutyStatus.REJECTED):
                continue

            duty_deadline_dt = datetime.combine(
                duty.duty_date, datetime.min.time()
            ).replace(hour=22, minute=0, second=0)

            stages = calculate_matching_stages(duty_deadline_dt, now)
            if not stages:
                continue

            # Lấy danh sách thành viên của ca trực
            team_ids = duty.team_id if isinstance(duty.team_id, list) else [duty.team_id]
            duty_user_ids = self.team_repo.get_user_ids_by_teams(team_ids)

            for uid in duty_user_ids:
                candidates.append(
                    ScannedCandidateTask(
                        task_type=TaskType.DUTY,
                        task_id=duty.id,
                        task_title=f"Trực nhật vệ sinh ngày {duty.duty_date.strftime('%d/%m/%Y')}",
                        user_id=uid,
                        deadline=duty_deadline_dt,
                        action_url="/dashboard/duties",
                        stages=stages,
                    )
                )

        return candidates
