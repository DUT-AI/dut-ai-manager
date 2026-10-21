"""
Web Push Notification Channel Adapter.
Sends push notifications to active PWA devices using SendWebPushNotificationUseCase.
"""

from loguru import logger

from app.reminder.application.send_web_push_notification_use_case import (
    SendWebPushNotificationUseCase,
)
from app.shared.infrastructure.notification.channel import (
    ChannelDeliveryResult,
    ChannelType,
    NotificationChannel,
)
from app.shared.infrastructure.notification_payload import NotificationPayload
from app.user.domain.entity import UserEntity as User


class WebPushNotificationChannel(NotificationChannel):
    """Channel adapter gửi thông báo đẩy Web Push PWA."""

    def __init__(self, send_web_push_use_case: SendWebPushNotificationUseCase):
        self.send_web_push_use_case = send_web_push_use_case

    @property
    def channel_type(self) -> ChannelType:
        return ChannelType.WEB_PUSH

    async def send(
        self, user: User, payload: NotificationPayload
    ) -> ChannelDeliveryResult:
        assert user.id is not None
        try:
            tag = (
                f"{payload.category.value}-{payload.task_id}"
                if payload.task_id
                else f"{payload.category.value}-notif"
            )
            cat_str = (
                payload.category.value
                if hasattr(payload.category, "value")
                else str(payload.category)
            )

            sent_count, failed_count = self.send_web_push_use_case.execute(
                user_id=user.id,
                title=payload.title,
                body=payload.content,
                action_url=payload.action_url,
                tag=tag,
                category=cat_str,
            )

            if sent_count > 0:
                logger.info(
                    f"WebPushNotificationChannel: Sent push to {sent_count} device(s) for user {user.id}"
                )
                return ChannelDeliveryResult(
                    channel=ChannelType.WEB_PUSH,
                    success=True,
                    status="SENT",
                )
            elif failed_count > 0:
                return ChannelDeliveryResult(
                    channel=ChannelType.WEB_PUSH,
                    success=False,
                    status="FAILED",
                    error_message=f"All {failed_count} device push attempts failed",
                )
            else:
                return ChannelDeliveryResult(
                    channel=ChannelType.WEB_PUSH,
                    success=False,
                    status="NO_SUBSCRIPTION",
                )
        except Exception as e:
            logger.error(
                f"WebPushNotificationChannel: Error sending push to user {user.id}: {e}"
            )
            return ChannelDeliveryResult(
                channel=ChannelType.WEB_PUSH,
                success=False,
                status="FAILED",
                error_message=str(e),
            )
