"""Change user password."""

from app.auth.infrastructure.repository import AccountRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.infrastructure.repository import UserRepository
from app.utils.password import get_password_hash, verify_password


class ChangePasswordUseCase:
    """Change user password."""

    def __init__(self, account_repo: AccountRepository, user_repo: UserRepository):
        self.account_repo = account_repo
        self.user_repo = user_repo

    def execute(
        self,
        user_id: int,
        old_password: str,
        new_password: str,
        confirm_password: str | None = None,
    ) -> bool:
        if confirm_password is not None and new_password != confirm_password:
            raise BadRequestException(
                status_code=400,
                message="Mật khẩu xác nhận không khớp",
            )

        user = self.user_repo.get_by_id(user_id)
        if not user or not user.id:
            raise BadRequestException(status_code=404, message="User not found")

        account_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user.id
                )
            ]
        )
        account = self.account_repo.get_one(account_qs)
        if not account:
            raise BadRequestException(status_code=400, message="Account not found")

        if not verify_password(old_password, account.hash_password):
            raise BadRequestException(status_code=400, message="Incorrect old password")

        account.hash_password = get_password_hash(new_password)
        self.account_repo.update(account)
        return True
