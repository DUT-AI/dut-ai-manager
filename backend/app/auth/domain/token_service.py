"""Token management service."""

from datetime import timedelta

from app.core.config import settings
from app.user.domain.entity import UserEntity
from app.utils.password import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
)


class TokenService:
    """Service responsible for generating and issuing authentication tokens."""

    @staticmethod
    def create_tokens(user: UserEntity) -> tuple[str, str]:
        """Create access and refresh tokens for user."""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        assert user.id is not None
        subject = TokenPayload(
            sub=user.id,
            name=user.name,
            email=user.email,
            roles=user.role_names,
            avatar=user.avatar_url or "",
            permissions=sorted(user.permissions),
        )
        access_token = create_access_token(
            subject=subject,
            expires_delta=access_token_expires,
        )
        refresh_token = create_refresh_token(subject=subject)
        return access_token, refresh_token
