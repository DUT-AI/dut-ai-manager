from collections.abc import Iterable

from dishka import Provider, Scope, provide
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.reminder.application.send_web_push_notification_use_case import (
    SendWebPushNotificationUseCase,
)
from app.reminder.infrastructure.repository import NotificationRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.email_service import EmailService
from app.shared.infrastructure.minio_service import MinioService
from app.shared.infrastructure.notification.discord_channel import (
    DiscordNotificationChannel,
)
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification.in_app_channel import (
    InAppNotificationChannel,
)
from app.shared.infrastructure.notification.web_push_channel import (
    WebPushNotificationChannel,
)
from app.shared.infrastructure.notification.zalo_channel import ZaloNotificationChannel
from app.shared.infrastructure.tts_service import TTSService
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class InfrastructureProvider(Provider):
    @provide(scope=Scope.APP)
    def get_engine(self) -> Engine:
        return create_engine(
            str(settings.SQLALCHEMY_DATABASE_URI),
            echo=settings.ENVIRONMENT == "local",
        )

    @provide(scope=Scope.REQUEST)
    def get_session(self, engine: Engine) -> Iterable[Session]:
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    @provide(scope=Scope.APP)
    def get_email_service(self) -> EmailService:
        return EmailService()

    @provide(scope=Scope.APP)
    def get_minio_service(self) -> MinioService:
        return MinioService()

    @provide(scope=Scope.APP)
    def get_discord_service(self) -> DiscordService:
        return DiscordService()

    @provide(scope=Scope.APP)
    def get_tts_service(self) -> TTSService:
        return TTSService()

    # Notification Channels
    @provide(scope=Scope.REQUEST)
    def get_in_app_channel(
        self, notification_repo: NotificationRepository
    ) -> InAppNotificationChannel:
        return InAppNotificationChannel(notification_repo)

    @provide(scope=Scope.REQUEST)
    def get_discord_channel(
        self, discord_service: DiscordService
    ) -> DiscordNotificationChannel:
        return DiscordNotificationChannel(discord_service)

    @provide(scope=Scope.REQUEST)
    def get_zalo_channel(self, zalo_bot: ZaloBotClient) -> ZaloNotificationChannel:
        return ZaloNotificationChannel(zalo_bot)

    @provide(scope=Scope.REQUEST)
    def get_web_push_channel(
        self, send_web_push_use_case: SendWebPushNotificationUseCase
    ) -> WebPushNotificationChannel:
        return WebPushNotificationChannel(send_web_push_use_case)

    # Unified Notification Hub Dispatcher
    @provide(scope=Scope.REQUEST)
    def get_unified_notification_dispatcher(
        self,
        user_repo: UserRepository,
        in_app_channel: InAppNotificationChannel,
        discord_channel: DiscordNotificationChannel,
        zalo_channel: ZaloNotificationChannel,
        web_push_channel: WebPushNotificationChannel,
    ) -> UnifiedNotificationDispatcher:
        return UnifiedNotificationDispatcher(
            user_repo=user_repo,
            in_app_channel=in_app_channel,
            discord_channel=discord_channel,
            zalo_channel=zalo_channel,
            web_push_channel=web_push_channel,
        )
