from datetime import timedelta

from pydantic import BaseModel

from app.meeting.infrastructure.repository import ParticipantRepository
from app.user.infrastructure.repository import UserRepository
from app.user.infrastructure.monthly_stats_repository import MonthlyUserStatsRepository
from app.shared.application.response import UserInfoResponse
from app.violation.domain.entity import ViolationType
from app.violation.infrastructure.repository import ViolationRepository


class ParticipationStats(BaseModel):
    user_id: int
    user: UserInfoResponse | None = None
    total_points: int = 0
    total_bonus_points: int = 0
    violation_count: int = 0
    month: int
    year: int
    total_sessions: int
    total_hours: float
    weekly_frequency: float
    current_streak: int
    longest_streak: int
    on_time_rate: float
    late_count: int
    absent_count: int


def _calc_streaks(checkin_dates: list, violation_dates: set) -> tuple[int, int]:
    """Tính current_streak và longest_streak."""
    if not checkin_dates:
        return 0, 0
    current = 0
    longest = 0
    for d in checkin_dates:
        if d in violation_dates:
            longest = max(longest, current)
            current = 0
        else:
            current += 1
    longest = max(longest, current)
    return current, longest


class GetParticipationAnalysisUseCase:
    def __init__(
        self,
        participant_repo: ParticipantRepository,
        violation_repo: ViolationRepository,
    ):
        self.participant_repo = participant_repo
        self.violation_repo = violation_repo

    def execute(self, user_id: int, month: int, year: int) -> ParticipationStats:
        participants = self.participant_repo.get_by_user_and_month(user_id, month, year)
        violations = self.violation_repo.get_by_month(user_id=user_id, month=month, year=year)

        # Tổng giờ
        total_hours = sum(
            (p.check_out_at - p.check_in_at).total_seconds() / 3600
            for p in participants
            if p.check_in_at and p.check_out_at
        )

        # Tần suất theo tuần
        active_weeks = {p.check_in_at.isocalendar().week for p in participants if p.check_in_at}
        # Số tuần trong tháng (thường 4-5)
        total_weeks = len({
            (p.check_in_at + timedelta(days=i)).isocalendar().week
            for p in participants if p.check_in_at
            for i in range(7)
            if (p.check_in_at + timedelta(days=i)).month == month
        }) or 4
        weekly_frequency = len(active_weeks) / total_weeks

        # Streak — dùng ngày có check-in, reset khi gặp violation
        checkin_dates = sorted({p.check_in_at.date() for p in participants if p.check_in_at})
        violation_dates = {v.date.date() for v in violations if v.date and v.type in (ViolationType.LATE, ViolationType.ABSENT)}
        current_streak, longest_streak = _calc_streaks(checkin_dates, violation_dates)

        late_count = sum(1 for v in violations if v.type == ViolationType.LATE)
        absent_count = sum(1 for v in violations if v.type == ViolationType.ABSENT)
        on_time_rate = 1.0 - (late_count / len(participants)) if participants else 1.0

        return ParticipationStats(
            user_id=user_id, month=month, year=year,
            total_sessions=len(participants),
            total_hours=round(total_hours, 2),
            weekly_frequency=round(weekly_frequency, 2),
            current_streak=current_streak,
            longest_streak=longest_streak,
            on_time_rate=round(on_time_rate, 2),
            late_count=late_count,
            absent_count=absent_count,
        )


class GetParticipationLeaderboardUseCase:
    """Bảng xếp hạng mức độ tham gia trong tháng."""

    def __init__(
        self,
        user_repo: UserRepository,
        stats_repo: MonthlyUserStatsRepository,
        analysis_uc: GetParticipationAnalysisUseCase,
    ):
        self.user_repo = user_repo
        self.stats_repo = stats_repo
        self.analysis_uc = analysis_uc

    def execute(self, month: int, year: int) -> list[ParticipationStats]:
        users = self.user_repo.get_active_users()
        stats_list = []
        for u in users:
            stat = self.analysis_uc.execute(u.id, month, year)
            
            # Add UserInfo
            stat.user = UserInfoResponse(**u.model_dump())
            
            # Calculate metrics
            stat.total_bonus_points = int(stat.total_hours)
            stat.violation_count = stat.late_count + stat.absent_count
            stat.total_points = stat.total_bonus_points - (2 * stat.late_count + 5 * stat.absent_count)
            
            stats_list.append(stat)
            
        # Sort theo total_points desc, tie-break bằng user.name asc
        return sorted(stats_list, key=lambda x: (-x.total_points, x.user.name.lower() if x.user and x.user.name else ""))
