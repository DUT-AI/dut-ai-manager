"""
WebPushService — Infrastructure Service bọc thư viện pywebpush.
Tuân thủ chuẩn VAPID RFC 8292 để gửi thông báo đẩy an toàn tới máy chủ Push (Google FCM, Apple APNs).
"""

import json

from loguru import logger

try:
    from pywebpush import WebPushException, webpush
except ImportError:
    webpush = None
    WebPushException = Exception

from app.core.config import Settings
from app.reminder.domain.entity import PushSubscription


class WebPushServiceException(Exception):
    """Lỗi cơ bản khi gửi Web Push."""

    pass


class DeadTokenException(WebPushServiceException):
    """Token hết hạn hoặc thiết bị đã hủy nhận thông báo (HTTP 404 / 410 Gone)."""

    pass


class WebPushService:
    """Service gửi Web Push Notification sử dụng cặp khóa VAPID."""

    def __init__(self, settings: Settings):
        self.public_key = settings.VAPID_PUBLIC_KEY
        self.private_key = settings.VAPID_PRIVATE_KEY
        self.claims_sub = settings.VAPID_CLAIMS_SUB

    def get_public_key(self) -> str:
        """Lấy VAPID Public Key trả về cho client."""
        return self.public_key

    def send_notification(
        self,
        subscription: PushSubscription,
        payload: dict,
        ttl: int = 86400,
    ) -> bool:
        """
        Gửi một thông báo đẩy tới một subscription cụ thể.
        :param subscription: Entity thông tin thiết bị
        :param payload: Dữ liệu JSON (title, body, icon, data, tag, ...)
        :param ttl: Thời gian sống của thông báo (mặc định 24 giờ)
        :return: True nếu gửi thành công
        """
        if not self.private_key:
            logger.warning("VAPID_PRIVATE_KEY chưa được cấu hình, bỏ qua gửi Web Push.")
            return False

        if webpush is None:
            logger.error("Thư viện pywebpush chưa được cài đặt.")
            return False

        subscription_info = {
            "endpoint": subscription.endpoint,
            "keys": {
                "p256dh": subscription.p256dh,
                "auth": subscription.auth,
            },
        }

        data_str = json.dumps(payload, ensure_ascii=False)
        vapid_claims = {"sub": self.claims_sub}

        try:
            response = webpush(
                subscription_info=subscription_info,
                data=data_str,
                vapid_private_key=self.private_key,
                vapid_claims=vapid_claims,
                ttl=ttl,
            )
            logger.info(
                f"Gửi Web Push thành công tới user={subscription.user_id}, "
                f"status={getattr(response, 'status_code', 200)}"
            )
            return True
        except WebPushException as ex:
            status_code = (
                getattr(ex.response, "status_code", None)
                if hasattr(ex, "response") and ex.response
                else None
            )
            logger.warning(
                f"Lỗi khi gửi Web Push tới endpoint {subscription.endpoint[:40]}...: "
                f"status={status_code}, error={str(ex)}"
            )
            if status_code in (404, 410):
                raise DeadTokenException(
                    f"Token expired or device unsubscribed: status {status_code}"
                ) from ex
            raise WebPushServiceException(
                f"Web Push delivery failed: {str(ex)}"
            ) from ex
        except Exception as e:
            logger.error(f"Lỗi không xác định khi gửi Web Push: {str(e)}")
            raise WebPushServiceException(f"Unexpected Web Push error: {str(e)}") from e
