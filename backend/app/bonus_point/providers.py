from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.bonus_point.application.use_cases import (
    CalculateActivityPointsUseCase,
    CreateBonusPointsUseCase,
    DeleteBonusPointUseCase,
    GetBonusPointsUseCase,
    RestoreBonusPointUseCase,
    UpdateBonusPointUseCase,
)
from app.bonus_point.infrastructure.repository import BonusPointRepository
from app.bonus_point.notification_handler import BonusPointNotificationHandler
from app.meeting.infrastructure.repository import ParticipantRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class BonusPointModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_bonus_point_repo(self, session: Session) -> BonusPointRepository:
        return BonusPointRepository(session)

    @provide
    def get_bonus_points_uc(self, repo: BonusPointRepository) -> GetBonusPointsUseCase:
        return GetBonusPointsUseCase(repo)

    @provide
    def create_bonus_points_uc(
        self, repo: BonusPointRepository
    ) -> CreateBonusPointsUseCase:
        return CreateBonusPointsUseCase(repo)

    @provide
    def update_bonus_point_uc(
        self, repo: BonusPointRepository
    ) -> UpdateBonusPointUseCase:
        return UpdateBonusPointUseCase(repo)

    @provide
    def delete_bonus_point_uc(
        self, repo: BonusPointRepository
    ) -> DeleteBonusPointUseCase:
        return DeleteBonusPointUseCase(repo)

    @provide
    def restore_bonus_point_uc(
        self, repo: BonusPointRepository
    ) -> RestoreBonusPointUseCase:
        return RestoreBonusPointUseCase(repo)

    @provide
    def get_calculate_activity_points_uc(
        self,
        participant_repo: ParticipantRepository,
        bonus_point_repo: BonusPointRepository,
    ) -> CalculateActivityPointsUseCase:
        return CalculateActivityPointsUseCase(participant_repo, bonus_point_repo)

    @provide
    def get_notification_handler(
        self,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ) -> BonusPointNotificationHandler:
        return BonusPointNotificationHandler(discord_service, zalo_bot, user_repo)
