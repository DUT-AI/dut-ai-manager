"""Authenticate user by email and password."""

from app.auth.domain.token_service import TokenService
from app.auth.infrastructure.repository import AccountRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository
from app.utils.password import verify_password


class AuthenticateUseCase:
    """Authenticate and issue tokens."""

    def __init__(
        self,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ):
        self.account_repo = account_repo
        self.user_repo = user_repo

    def execute(self, email: str, password: str) -> tuple[UserEntity, str, str]:
        # 1. Tìm user theo email sử dụng get_one & QuerySupport
        # Cần include role và permissions để to_entity trả về đầy đủ permissions
        user_qs = build_query_support(
            filters=[
                FilterCriterion(field="email", operator=FilterOperator.EQ, value=email)
            ],
            include=[
                "roles",
                "roles.role_permissions",
                "roles.role_permissions.permission",
            ],
        )
        user = self.user_repo.get_one(user_qs)

        if not user:
            raise BadRequestException(status_code=401, message="User not found")

        if user.status == UserStatus.INACTIVE:
            raise BadRequestException(status_code=401, message="Account is inactive")

        # 2. Tìm account theo user_id sử dụng get_one & QuerySupport
        account_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user.id
                )
            ]
        )
        account = self.account_repo.get_one(account_qs)

        if not account or not verify_password(password, account.hash_password):
            raise BadRequestException(
                status_code=401, message="Incorrect email or password"
            )

        access_token, refresh_token = TokenService.create_tokens(user)
        return user, access_token, refresh_token
