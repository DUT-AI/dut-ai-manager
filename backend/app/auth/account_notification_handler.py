import asyncio

from loguru import logger

from app.auth.domain.events import AccountCreated, ForgotPasswordRequested
from app.shared.infrastructure.discord_service import DiscordService
from app.shared.infrastructure.email_service import EmailService
from app.user.infrastructure.repository import UserRepository
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient


class AccountNotificationHandler:
    """Handles Account events to send notifications (Email/Discord/Zalo)."""

    def __init__(
        self,
        email_service: EmailService,
        discord_service: DiscordService,
        zalo_bot: ZaloBotClient,
        user_repo: UserRepository,
    ):
        self.email_service = email_service
        self.discord_service = discord_service
        self.zalo_bot = zalo_bot
        self.user_repo = user_repo

    async def handle(self, event: AccountCreated | ForgotPasswordRequested) -> None:
        """EntryPoint cho EventBus để điều hướng sự kiện."""
        if isinstance(event, AccountCreated):
            await self._handle_account_created(event)
        elif isinstance(event, ForgotPasswordRequested):
            await self._handle_forgot_password(event)

    async def _handle_account_created(self, event: AccountCreated) -> None:
        """Send welcome email when user account is created in background."""
        logger.info(f"Scheduling welcome email to {event.email} in background")

        def send_email_sync():
            try:
                self.email_service.send_new_account_email(
                    to_email=event.email, name=event.name, password=event.password
                )
                logger.info(
                    f"Background: Welcome email sent successfully to {event.email}"
                )
            except Exception as e:
                logger.error(
                    f"Background: Failed to send welcome email to {event.email}: {e}"
                )

        asyncio.create_task(asyncio.to_thread(send_email_sync))

    async def _handle_forgot_password(self, event: ForgotPasswordRequested) -> None:
        """Send reset password notifications via Email, Zalo, and Discord."""
        logger.info(
            f"Scheduling forgot password notifications for user_id={event.user_id} in background"
        )

        # 1. Gửi Email (Chạy đồng bộ trong ThreadPool vì dùng smtplib block)
        def send_email_sync():
            try:
                self.email_service.send_forgot_password_email(
                    to_email=event.email,
                    name=event.name,
                    password=event.password,
                )
                logger.info(
                    f"Background: Reset password email sent successfully to {event.email}"
                )
            except Exception as e:
                logger.error(
                    f"Background: Failed to send reset password email to {event.email}: {e}"
                )

        asyncio.create_task(asyncio.to_thread(send_email_sync))

        # 2. Lấy thông tin user để kiểm tra Zalo và Discord
        user = self.user_repo.get_by_id(event.user_id)
        if not user:
            logger.error(f"User {event.user_id} not found in forgot password handler")
            return

        # 3. Gửi thông báo Zalo
        if user.zalo_bot_id:
            zalo_bot_id = user.zalo_bot_id
            zalo_text = (
                f"🔑 KHÔI PHỤC MẬT KHẨU THÀNH CÔNG\n\n"
                f"Chào {user.name},\n"
                f"Yêu cầu khôi phục mật khẩu cho tài khoản {user.email} đã được xử lý.\n"
                f"Mật khẩu mới của bạn là: {event.password}\n\n"
                f"Vui lòng đăng nhập và đổi mật khẩu ngay lập tức để bảo mật tài khoản."
            )

            async def send_zalo_async():
                try:
                    await self.zalo_bot.send_message(
                        chat_id=zalo_bot_id, text=zalo_text
                    )
                    logger.info(
                        f"Background: Sent Zalo forgot-password notification to {user.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Background: Failed to send Zalo forgot-password notification to {user.name}: {e}"
                    )

            asyncio.create_task(send_zalo_async())

        # 4. Gửi thông báo Discord
        if user.discord_id and str(user.discord_id).isdigit():
            embed = {
                "title": "🔑 KHÔI PHỤC MẬT KHẨU THÀNH CÔNG",
                "description": f"Yêu cầu khôi phục mật khẩu cho tài khoản **{user.email}** đã được xử lý.",
                "color": 0x3498DB,
                "fields": [
                    {"name": "👤 Tài khoản", "value": user.email, "inline": True},
                    {
                        "name": "🔑 Mật khẩu mới",
                        "value": f"`{event.password}`",
                        "inline": True,
                    },
                ],
                "footer": {"text": "DUT AI Manager • Hệ thống tự động"},
            }

            async def send_discord_async():
                try:
                    await self.discord_service.send_message_to_user(
                        user_id=str(user.discord_id),
                        content=f"Chào <@{user.discord_id}>! Mật khẩu mới của bạn đã được khởi tạo thành công.",
                        embed=embed,
                    )
                    logger.info(
                        f"Background: Sent Discord forgot-password notification to {user.name}"
                    )
                except Exception as e:
                    logger.error(
                        f"Background: Failed to send Discord forgot-password notification to {user.name}: {e}"
                    )

            asyncio.create_task(send_discord_async())
