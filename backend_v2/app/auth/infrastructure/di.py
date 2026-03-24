from app.auth.application.use_cases.change_password import \
  ChangePasswordUseCase
from app.auth.application.use_cases.login import LoginUseCase
from app.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from app.auth.domain.interfaces import (IAccountCreator, IAuthUserRepository,
                                        IPasswordHasher,
                                        ITokenService, IAuthQueryService)
from app.auth.infrastructure.account_creator import AccountCreatorService
from app.auth.infrastructure.auth_user_repository import AuthUserRepository
from app.auth.infrastructure.bcrypt_hasher import BcryptPasswordHasher
from app.auth.infrastructure.jwt_service import JwtTokenService
from app.auth.infrastructure.auth_query_service import SQLAlchemyAuthQueryService
from app.settings import JWTSetting
from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession


class AuthProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_jwt_settings(self) -> JWTSetting:
        return JWTSetting()

    @provide(scope=Scope.APP)
    def provide_token_service(self, settings: JWTSetting) -> ITokenService:
        return JwtTokenService(settings)

    @provide(scope=Scope.APP)
    def provide_password_hasher(self) -> IPasswordHasher:
        return BcryptPasswordHasher()

    @provide(scope=Scope.REQUEST)
    def provide_auth_repository(self, session: AsyncSession) -> IAuthUserRepository:
        return AuthUserRepository(session)

    @provide(scope=Scope.REQUEST)
    def provide_auth_query_service(self, session: AsyncSession) -> IAuthQueryService:
        return SQLAlchemyAuthQueryService(session)

    @provide(scope=Scope.REQUEST)
    def provide_account_creator(
        self, session: AsyncSession, hasher: IPasswordHasher
    ) -> IAccountCreator:
        return AccountCreatorService(session, hasher)

    @provide(scope=Scope.REQUEST)
    def provide_login_use_case(
        self,
        hasher: IPasswordHasher,
        token_service: ITokenService,
        auth_query: IAuthQueryService,
    ) -> LoginUseCase:
        return LoginUseCase(hasher, token_service, auth_query)

    @provide(scope=Scope.REQUEST)
    def provide_refresh_token_use_case(
        self,
        repo: IAuthUserRepository,
        token_service: ITokenService,
    ) -> RefreshTokenUseCase:
        return RefreshTokenUseCase(repo, token_service)

    @provide(scope=Scope.REQUEST)
    def provide_change_password_use_case(
        self,
        repo: IAuthUserRepository,
        hasher: IPasswordHasher,
    ) -> ChangePasswordUseCase:
        return ChangePasswordUseCase(repo, hasher)
