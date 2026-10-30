from datetime import UTC, datetime, timedelta

from app.bonus_point.domain.entity import BonusPoint
from app.bonus_point.domain.value_objects import BonusPointType
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.meeting.infrastructure.repository import ParticipantRepository


class CalculateActivityPointsUseCase:
    def __init__(
        self,
        participant_repo: ParticipantRepository,
        bonus_point_repo: BonusPointRepository,
    ):
        self.participant_repo = participant_repo
        self.bonus_point_repo = bonus_point_repo

    def execute(self, since: datetime | None = None) -> int:
        if since is None:
            since = datetime.now(UTC) - timedelta(hours=1)

        participants = self.participant_repo.get_completed_since(since)

        count = 0
        for p in participants:
            if p.check_in_at and p.check_out_at:
                duration = max(0.0, (p.check_out_at - p.check_in_at).total_seconds())
                hours = duration / 3600
                points = int(round(hours))

                if points > 0:
                    existing = self.bonus_point_repo.get_by_user_and_reason_and_date(
                        user_id=p.user_id,
                        reason="Hoạt động tại CLB",
                        date=p.check_out_at.date(),
                    )

                    if not existing:
                        bonus = BonusPoint(
                            user_id=p.user_id,
                            points=points,
                            reason=f"Hoạt động tại CLB: {hours:.2f} giờ",
                            date=datetime.now(UTC),
                            type=BonusPointType.CLUB_ACTIVITY,
                        )
                        self.bonus_point_repo.add(bonus)
                        count += 1
        return count
