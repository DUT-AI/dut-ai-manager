"""
Auth Application Use Cases — business logic layer.
"""

import random
import string
from datetime import timedelta

from app.auth.domain.entity import Account
from app.auth.domain.events import ForgotPasswordRequested
from app.auth.infrastructure.repository import AccountRepository
from app.core.config import settings
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.event_bus import EventBus
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository
from app.utils.password import (
    TokenPayload,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    hash_password,
    verify_password,
)


class BaseAuthUseCase:
    """Base logic for auth operations."""

    def __init__(self, account_repo: AccountRepository, user_repo: UserRepository):
        self.account_repo = account_repo
        self.user_repo = user_repo

    def create_tokens(self, user: UserEntity) -> tuple[str, str]:
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


class AuthenticateUseCase(BaseAuthUseCase):
    """Authenticate and issue tokens."""

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

        access_token, refresh_token = self.create_tokens(user)
        return user, access_token, refresh_token


class AuthenticateZaloPhoneUseCase(BaseAuthUseCase):
    """Authenticate via Zalo Mini App Phone Token."""

    def _resolve_phone_number_from_zalo(
        self, phone_token: str, zalo_access_token: str | None = None
    ) -> str:
        """Call Zalo Open API to decrypt phone token using App Secret."""
        import requests

        app_secret = settings.ZALO_APP_SECRET
        access_token = zalo_access_token or settings.ZALO_OA_ACCESS_TOKEN

        headers = {}
        if access_token:
            headers["access_token"] = access_token
        if app_secret:
            headers["secret_key"] = app_secret

        try:
            url = "https://graph.zalo.me/v2.0/me/info"
            res = requests.get(
                url,
                headers=headers,
                params={"code": phone_token},
                timeout=10,
            )
            data = res.json()
            if data.get("error") == 0 and "data" in data and "number" in data["data"]:
                raw_number = str(data["data"]["number"])
                # Normalize phone number (84xxx -> 0xxx)
                if raw_number.startswith("84"):
                    raw_number = "0" + raw_number[2:]
                return raw_number
            else:
                err_msg = data.get("message") or "Không thể xác thực số điện thoại Zalo"
                raise BadRequestException(status_code=400, message=err_msg)
        except BadRequestException:
            raise
        except Exception as exc:
            raise BadRequestException(
                status_code=400,
                message=f"Lỗi khi kết nối Zalo API giải mã SĐT: {str(exc)}",
            ) from exc

    def execute(
        self, phone_token: str, zalo_access_token: str | None = None
    ) -> tuple[UserEntity, str, str]:
        # 1. Giải mã phone_token từ Zalo API
        phone_number = self._resolve_phone_number_from_zalo(
            phone_token, zalo_access_token
        )

        # 2. Tìm user theo phone_number
        # Hỗ trợ cả 2 định dạng: 0905xxx hoặc 84905xxx
        phone_candidates = [phone_number]
        if phone_number.startswith("0"):
            phone_candidates.append("84" + phone_number[1:])
        elif phone_number.startswith("84"):
            phone_candidates.append("0" + phone_number[2:])

        user = None
        for p in phone_candidates:
            user_qs = build_query_support(
                filters=[
                    FilterCriterion(
                        field="phone_number", operator=FilterOperator.EQ, value=p
                    )
                ],
                include=[
                    "roles",
                    "roles.role_permissions",
                    "roles.role_permissions.permission",
                ],
            )
            user = self.user_repo.get_one(user_qs)
            if user:
                break

        if not user:
            raise BadRequestException(
                status_code=404,
                message=(
                    f"Số điện thoại {phone_number} chưa được đăng ký tài khoản "
                    f"trong hệ thống DUT AI"
                ),
            )

        if user.status == UserStatus.INACTIVE:
            raise BadRequestException(status_code=401, message="Account is inactive")

        access_token, refresh_token = self.create_tokens(user)
        return user, access_token, refresh_token


class RefreshTokenUseCase(BaseAuthUseCase):
    """Issue new tokens given a valid refresh token."""

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

        return self.create_tokens(user)


class ChangePasswordUseCase(BaseAuthUseCase):
    """Change user password."""

    def execute(self, user: UserEntity, old_password: str, new_password: str) -> bool:
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


class CreateAccountUseCase:
    """Creates a new DB account and strong random password. Typically used internally by User generation."""

    def __init__(self, account_repo: AccountRepository):
        self.account_repo = account_repo

    def execute(self, user_id: int | None = None) -> tuple[Account, str]:
        password = self._generate_strong_password()
        account = Account(hash_password=hash_password(password), user_id=user_id)
        saved = self.account_repo.add(account)
        return saved, password

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


class ForgotPasswordUseCase(BaseAuthUseCase):
    """Reset user password and send email."""

    def __init__(
        self,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ):
        super().__init__(account_repo, user_repo)

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
