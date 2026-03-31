from typing import Tuple

from app.auth.application.dtos import (
    LoginRequestDTO,
    TokenResponseDTO,
    UserAuthContextDTO,
)
from app.auth.domain.exceptions import (
    InvalidCredentialsException,
    UserInactiveException,
)
from app.auth.domain.interfaces import IAuthQueryService, IPasswordHasher, ITokenService

from app.auth.application.dtos import JWTPayload


class LoginUseCase:
    def __init__(
        self,
        password_hasher: IPasswordHasher,
        token_service: ITokenService,
        auth_query: IAuthQueryService,
    ):
        self.password_hasher = password_hasher
        self.token_service = token_service
        self.auth_query = auth_query

    async def execute(self, payload: LoginRequestDTO) -> TokenResponseDTO:
        user_auth = await self.auth_query.get_user_auth_context_by_email(payload.email)

        if not user_auth:
            raise InvalidCredentialsException()

        # Check if user has no password yet (e.g., social login only)
        if not user_auth.hashed_password:
            raise InvalidCredentialsException()

        if not self.password_hasher.verify(payload.password, user_auth.hashed_password):
            raise InvalidCredentialsException()

        if not user_auth.is_active:
            raise UserInactiveException()

        access_token, refresh_token = self.create_tokens(user_auth)

        return TokenResponseDTO(access_token=access_token, refresh_token=refresh_token)

    def create_tokens(self, user_auth: UserAuthContextDTO) -> Tuple[str, str]:
        """Create access and refresh tokens for user with embedded user info"""

        # Build extra claims for JWT
        extra_claims = JWTPayload(
            sub=str(user_auth.id),
            email=user_auth.email,
            name=user_auth.name,
            role=user_auth.role_name,
            avatar=user_auth.avatar_url,
            permissions=user_auth.permissions,
        )

        access_token = self.token_service.create_access_token(extra_claims)
        refresh_token = self.token_service.create_refresh_token(
            {"sub": str(user_auth.id)}
        )
        return access_token, refresh_token
