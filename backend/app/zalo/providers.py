from dishka import Provider, Scope, provide
from app.zalo.application.use_cases import (
    GetZaloLoginUrlUseCase,
    BindZaloAccountUseCase,
    GenerateBotBindCodeUseCase,
    HandleBotWebhookUseCase,
    SendZaloNotificationUseCase
)
from app.zalo.infrastructure.zalo_client import ZaloClient
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient
from app.user.infrastructure.repository import UserRepository

class ZaloModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def get_zalo_client(self) -> ZaloClient:
        return ZaloClient()

    @provide(scope=Scope.APP)
    def get_zalo_bot_client(self) -> ZaloBotClient:
        return ZaloBotClient()

    @provide
    def get_login_url_uc(self) -> GetZaloLoginUrlUseCase:
        return GetZaloLoginUrlUseCase()

    @provide
    def get_bind_account_uc(self, zalo_client: ZaloClient, user_repo: UserRepository) -> BindZaloAccountUseCase:
        return BindZaloAccountUseCase(zalo_client, user_repo)

    @provide
    def get_generate_bot_code_uc(self, repo: UserRepository) -> GenerateBotBindCodeUseCase:
        return GenerateBotBindCodeUseCase(repo)

    @provide
    def get_handle_bot_webhook_uc(self, bot_client: ZaloBotClient, repo: UserRepository) -> HandleBotWebhookUseCase:
        return HandleBotWebhookUseCase(bot_client, repo)

    @provide
    def get_send_notification_uc(self, zalo_client: ZaloClient, bot_client: ZaloBotClient) -> SendZaloNotificationUseCase:
        return SendZaloNotificationUseCase(zalo_client, bot_client)
