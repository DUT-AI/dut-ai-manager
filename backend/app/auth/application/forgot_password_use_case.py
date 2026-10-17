"""Reset user password and send email."""

import random
import string

from app.auth.domain.events import ForgotPasswordRequested
from app.auth.infrastructure.repository import AccountRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserStatus
from app.user.infrastructure.repository import UserRepository
from app.utils.password import get_password_hash


class ForgotPasswordUseCase:
    """Reset user password and send email."""

    def __init__(
        self,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ):
        self.account_repo = account_repo
        self.user_repo = user_repo

    async def execute(self, email: str) -> bool:
        # 1. Tìm user theo email
        user_qs = build_query_support(
            filters=[
                FilterCriterion(field="email", operator=FilterOperator.EQ, value=email)
            ]
        )
        user = self.user_repo.get_one(user_qs)
        if not user or user.id is None:
            raise BadRequestException(
                status_code=404, message="Email không tồn tại trong hệ thống"
            )

        if user.status == UserStatus.INACTIVE:
            raise BadRequestException(
                status_code=400, message="Tài khoản này đang bị khóa"
            )

        user_id = user.id

        # 2. Tìm account tương ứng
        account_qs = build_query_support(
            filters=[
                FilterCriterion(
                    field="user_id", operator=FilterOperator.EQ, value=user_id
                )
            ]
        )
        account = self.account_repo.get_one(account_qs)
        if not account:
            raise BadRequestException(
                status_code=404, message="Không tìm thấy tài khoản tương ứng"
            )

        # 3. Tạo mật khẩu mới
        new_password = self._generate_strong_password()

        # 4. Hash và lưu
        account.hash_password = get_password_hash(new_password)
        self.account_repo.update(account)

        # 5. Phát hành Domain Event
        await EventBus.publish(
            ForgotPasswordRequested(
                user_id=user_id,
                email=user.email,
                name=user.name,
                password=new_password,
            )
        )

        return True

    def _generate_strong_password(self) -> str:
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "@#$!%*?&"

        password_chars = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(symbols),
        ]
        all_chars = lowercase + uppercase + digits + symbols
        length = random.randint(10, 12)
        for _ in range(length - 4):
            password_chars.append(random.choice(all_chars))

        random.shuffle(password_chars)
        return "".join(password_chars)
