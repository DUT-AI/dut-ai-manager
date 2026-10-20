"""
Reminder Dispatcher.
Handles sending Discord DM embeds, creating In-App Notifications, and recording audit logs into unified Notification repository.
"""

from datetime import datetime
from loguru import logger

from app.core.config import settings
from app.reminder.application.embed_builder import build_reminder_embed, format_remaining_time
from app.reminder.domain.entity import (
    Notification,
    ReminderStage,
    ReminderStatus,
    TaskType,
)
from app.reminder.infrastructure.repository import NotificationRepository
from app.shared.infrastructure.discord_service import DiscordService
from app.user.infrastructure.repository import UserRepository


class ReminderDispatcher:
    def __init__(
        self,
        notification_repo: NotificationRepository,
        user_repo: UserRepository,
        discord_service: DiscordService,
    ):
        self.notification_repo = notification_repo
        self.user_repo = user_repo
        self.discord_service = discord_service

    async def dispatch(
        self,
        task_type: TaskType,
        task_id: int,
        task_title: str,
        user_id: int,
        deadline: datetime,
        stage: ReminderStage,
        action_url: str,
        now: datetime,
    ) -> ReminderStatus:
        """Gửi thông báo đa kênh (Discord DM + In-App Web) và lưu vào bảng notifications duy nhất."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return ReminderStatus.FAILED

        hours_left = max(0.1, (deadline - now).total_seconds() / 3600.0)
        deadline_str = deadline.strftime("%d/%m/%Y %H:%M")
        time_left_str = format_remaining_time(hours_left)

        # 1. Gửi Discord DM nếu người dùng có liên kết discord_id
        status = ReminderStatus.SENT
        err_msg: str | None = None

        if not user.discord_id:
            status = ReminderStatus.NO_DISCORD_ID
        else:
            embed = build_reminder_embed(
                task_type=task_type,
                task_title=task_title,
                deadline_str=deadline_str,
                hours_left=hours_left,
                stage=stage,
                action_url=f"{settings.FRONTEND_URL}{action_url}" if hasattr(settings, "FRONTEND_URL") else action_url,
            )
            try:
                await self.discord_service.send_message_to_user(
                    user_id=user.discord_id,
                    embed=embed,
                )
            except Exception as e:
                err_msg = str(e)
                if "50007" in err_msg or "Cannot send messages to this user" in err_msg:
                    status = ReminderStatus.DM_BLOCKED
                else:
                    status = ReminderStatus.FAILED
                logger.warning(
                    f"Không thể gửi Discord DM nhắc nhở tới user {user_id} (discord_id: {user.discord_id}): {err_msg}"
                )

        # 2. Tạo bản ghi Notification thống nhất (hiển thị Web + metadata kỹ thuật chống lặp)
        notif_entity = Notification.create_deadline_reminder(
            user_id=user_id,
            task_type=task_type,
            task_id=task_id,
            task_title=task_title,
            deadline_str=deadline_str,
            time_left_str=time_left_str,
            stage=stage,
            action_url=action_url,
            now=now,
            discord_status=status,
            error_message=err_msg,
        )
        self.notification_repo.add(notif_entity)

        return status
