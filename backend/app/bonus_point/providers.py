from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.bonus_point.application.use_cases import CalculateActivityPointsUseCase
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.meeting.infrastructure.repository import ParticipantRepository


class BonusPointModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_bonus_point_repo(self, session: Session) -> BonusPointRepository:
        return BonusPointRepository(session)

    @provide
    def get_calculate_activity_points_uc(
        self,
        participant_repo: ParticipantRepository,
        bonus_point_repo: BonusPointRepository,
    ) -> CalculateActivityPointsUseCase:
        return CalculateActivityPointsUseCase(participant_repo, bonus_point_repo)
