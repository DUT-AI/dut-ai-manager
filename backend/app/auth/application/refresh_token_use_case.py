"""Issue new tokens given a valid refresh token."""

from app.auth.domain.token_service import TokenService
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.infrastructure.repository import UserRepository
from app.utils.password import decode_refresh_token


class RefreshTokenUseCase:
    """Issue new tokens given a valid refresh token."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def execute(self, refresh_token_str: str) -> tuple[str, str]:
        payload = decode_refresh_token(refresh_token_str)
        if not payload:
            raise BadRequestException(
                status_code=400, message="Invalid or expired refresh token"
            )

        # Sử dụng get_one để load role/permissions
        user_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="id", operator=FilterOperator.EQ, value=payload.sub
                )
            ],
            include=[
                "roles",
                "roles.role_permissions",
                "roles.role_permissions.permission",
            ],
        )
        user = self.user_repo.get_one(user_qs)
        if not user:
            raise BadRequestException(status_code=400, message="User not found")

        return TokenService.create_tokens(user)
