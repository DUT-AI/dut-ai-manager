"""Authenticate via Zalo Mini App Phone Token."""

from app.auth.domain.token_service import TokenService
from app.auth.infrastructure.repository import AccountRepository
from app.core.config import settings
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository


class AuthenticateZaloPhoneUseCase:
    """Authenticate via Zalo Mini App Phone Token."""

    def __init__(
        self,
        account_repo: AccountRepository,
        user_repo: UserRepository,
    ):
        self.account_repo = account_repo
        self.user_repo = user_repo

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

        access_token, refresh_token = TokenService.create_tokens(user)
        return user, access_token, refresh_token
