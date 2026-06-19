import calendar
from typing import Literal
from pydantic import BaseModel

from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.meeting.infrastructure.repository import MeetingRepository
from app.violation.domain.entity import ViolationType
from app.violation.infrastructure.repository import ViolationRepository


class ActivityTrendItem(BaseModel):
    label: str
    total_bonus_points: int
    violation_count: int


class GetActivityTrendUseCase:
    """Lấy dữ liệu xu hướng hoạt động (điểm cộng + vi phạm) theo tuần hoặc tháng."""

    def __init__(
        self,
        bonus_point_repo: BonusPointRepository,
        violation_repo: ViolationRepository,
        meeting_repo: MeetingRepository,
    ):
        self.bonus_point_repo = bonus_point_repo
        self.violation_repo = violation_repo
        self.meeting_repo = meeting_repo

    def execute(
        self, month: int, year: int, mode: Literal["week", "month"] = "week"
    ) -> list[ActivityTrendItem]:
        if mode == "week":
            return self._aggregate_by_week(month, year)
        else:
            return self._aggregate_by_month(month, year)

    def _aggregate_by_week(self, month: int, year: int) -> list[ActivityTrendItem]:
        from datetime import date, timedelta
        import calendar

        last_day = calendar.monthrange(year, month)[1]
        end_date = date(year, month, last_day)

        WEEKS_COUNT = 24
        meetings = []
        violations = []

        curr_m = month
        curr_y = year
        for _ in range(6):
            meetings.extend(self.meeting_repo.get_all_with_participants(month=curr_m, year=curr_y))
            violations.extend(self.violation_repo.get_by_month(user_id=None, month=curr_m, year=curr_y))

            curr_m -= 1
            if curr_m == 0:
                curr_m = 12
                curr_y -= 1

        items = []
        current_end = end_date
        for i in range(WEEKS_COUNT):
            current_start = current_end - timedelta(days=6)

            label = current_start.strftime('%d/%m')

            # Calculate violations
            week_v = [
                v for v in violations
                if v.date and current_start <= v.date.date() <= current_end
                and v.type in (ViolationType.LATE, ViolationType.ABSENT)
            ]

            # Calculate attendance hours
            week_meetings = [
                m for m in meetings
                if m.start_time and current_start <= m.start_time.date() <= current_end
            ]
            total_hours = 0.0
            for m in week_meetings:
                if m.participants:
                    for p in m.participants:
                        if p.check_in_at and p.check_out_at:
                            total_hours += (p.check_out_at - p.check_in_at).total_seconds() / 3600.0

            items.append(
                ActivityTrendItem(
                    label=label,
                    total_bonus_points=int(total_hours),
                    violation_count=len(week_v),
                )
            )

            current_end = current_start - timedelta(days=1)

        items.reverse()
        return items

    def _aggregate_by_month(self, month: int, year: int) -> list[ActivityTrendItem]:
        items = []
        for m in range(1, month + 1):
            label = f"Tháng {m}"

            violations = self.violation_repo.get_by_month(user_id=None, month=m, year=year)
            v_count = sum(
                1 for v in violations if v.type in (ViolationType.LATE, ViolationType.ABSENT)
            )

            meetings = self.meeting_repo.get_all_with_participants(month=m, year=year)
            total_hours = 0.0
            for mtg in meetings:
                if mtg.participants:
                    for p in mtg.participants:
                        if p.check_in_at and p.check_out_at:
                            total_hours += (p.check_out_at - p.check_in_at).total_seconds() / 3600.0

            items.append(
                ActivityTrendItem(
                    label=label,
                    total_bonus_points=int(total_hours),
                    violation_count=v_count,
                )
            )

        return items
