from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.auth.account_notification_handler import AccountNotificationHandler
from app.auth.application import (
    AuthenticateUseCase,
    AuthenticateZaloPhoneUseCase,
    ChangePasswordUseCase,
    CreateAccountUseCase,
    ForgotPasswordUseCase,
    GetMeUseCase,
    RefreshTokenUseCase,
    UserAccountHandler,
)
from app.auth.domain.service import AuthService
from app.auth.domain.token_service import TokenService
from app.auth.infrastructure.repository import AccountRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.email_service import EmailService
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class AuthModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide(scope=Scope.APP)
    def get_auth_service(self) -> AuthService:
        return AuthService()

    @provide(scope=Scope.APP)
    def get_token_service(self) -> TokenService:
        return TokenService()

    @provide
    def get_account_repo(self, session: Session) -> AccountRepository:
        return AccountRepository(session)

    @provide
    def get_user_repo(self, session: Session) -> UserRepository:
        return UserRepository(session)

    @provide
    def authenticate_uc(
        self, account_repo: AccountRepository, user_repo: UserRepository
    ) -> AuthenticateUseCase:
        return AuthenticateUseCase(account_repo, user_repo)

    @provide
    def authenticate_zalo_phone_uc(
        self, account_repo: AccountRepository, user_repo: UserRepository
    ) -> AuthenticateZaloPhoneUseCase:
        return AuthenticateZaloPhoneUseCase(account_repo, user_repo)

    @provide
    def refresh_token_uc(self, user_repo: UserRepository) -> RefreshTokenUseCase:
        return RefreshTokenUseCase(user_repo)

    @provide
    def change_password_uc(
        self, account_repo: AccountRepository, user_repo: UserRepository
    ) -> ChangePasswordUseCase:
        return ChangePasswordUseCase(account_repo, user_repo)

    @provide
    def get_me_uc(self, user_repo: UserRepository) -> GetMeUseCase:
        return GetMeUseCase(user_repo)

    @provide
    def create_account_uc(
        self, account_repo: AccountRepository
    ) -> CreateAccountUseCase:
        return CreateAccountUseCase(account_repo)

    @provide
    def get_user_account_handler(
        self, auth_service: AuthService, account_repo: AccountRepository
    ) -> UserAccountHandler:
        return UserAccountHandler(auth_service, account_repo)

    @provide
    def get_account_notif_handler(
        self,
        email_service: EmailService,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ) -> AccountNotificationHandler:
        return AccountNotificationHandler(
            email_service, discord_service, zalo_bot, user_repo
        )

    @provide
    def forgot_password_uc(
        self,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ) -> ForgotPasswordUseCase:
        return ForgotPasswordUseCase(account_repo, user_repo)
