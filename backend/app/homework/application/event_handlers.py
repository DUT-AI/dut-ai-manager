import asyncio

from loguru import logger

from app.homework.domain.value_objects import HomeworkAssigned, HomeworkGraded
from app.homework.infrastructure.homework_repository import HomeworkRepository
from app.shared.application.event_handler import EventHandler
from app.shared.infrastructure.notification.dispatcher import (
    UnifiedNotificationDispatcher,
)
from app.shared.infrastructure.notification_payload import (
    NotificationCategory,
    NotificationLevel,
    NotificationPayload,
)
from app.user.infrastructure.repository import UserRepository


class HomeworkNotificationHandler(EventHandler):
    """Xử lý gửi thông báo đa kênh (In-App DB, Discord, Zalo, Web Push) khi có bài tập mới."""

    def __init__(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
    ):
        self.dispatcher = dispatcher
        self.homework_repo = homework_repo
        self.user_repo = user_repo

    async def handle(self, event: HomeworkAssigned) -> None:
        """Thông báo cho người dùng khi họ được giao bài tập mới."""
        try:
            logger.info(f"Handling HomeworkAssigned for homework {event.homework_id}")
            homework = self.homework_repo.get_by_id(event.homework_id)
            if not homework:
                logger.error(f"Homework {event.homework_id} not found in handler")
                return

            users = self.user_repo.get_by_ids(event.assignee_ids)
            if not users:
                logger.warning(f"No users found for assignee_ids: {event.assignee_ids}")
                return

            asyncio.create_task(self._send_notifications_task(homework, users))
            logger.info(
                f"Notifications for homework {event.homework_id} have been scheduled in background"
            )

        except Exception as e:
            logger.error(f"Error in HomeworkNotificationHandler: {e}")

    async def _send_notifications_task(self, homework, users) -> None:
        """Hàm chạy ngầm để gửi thông báo qua UnifiedNotificationDispatcher."""
        try:
            deadline_str = homework.deadline.strftime("%H:%M ngày %d/%m/%Y")

            fields = [{"name": "⏰ Hạn nộp", "value": deadline_str, "inline": True}]
            if homework.link:
                fields.append(
                    {
                        "name": "🔗 Đường dẫn bài tập",
                        "value": str(homework.link),
                        "inline": False,
                    }
                )

            for user in users:
                assert user.id is not None
                payload = NotificationPayload(
                    user_id=user.id,
                    title="📚 BÀI TẬP MỚI ĐƯỢC GIAO",
                    content=(
                        f"Chào {user.name}!\n"
                        f"Bạn vừa được giao bài tập mới: {homework.title}\n"
                        f"Vui lòng kiểm tra và nộp bài trước hạn chót."
                    ),
                    category=NotificationCategory.HOMEWORK,
                    level=NotificationLevel.INFO,
                    image_asset="meme-hoc-bai.webp",
                    fields=fields,
                    action_url=homework.link or f"/homework/{homework.id}",
                    task_type="HOMEWORK",
                    task_id=homework.id,
                )
                await self.dispatcher.dispatch(payload)

            logger.info(f"Finished sending notifications for homework {homework.id}")
        except Exception as e:
            logger.error(
                f"Unexpected error in background homework notification task: {e}"
            )


class HomeworkGradedNotificationHandler(EventHandler):
    """Xử lý gửi thông báo kết quả chấm điểm (Feedback) qua đa kênh."""

    def __init__(
        self,
        dispatcher: UnifiedNotificationDispatcher,
        homework_repo: HomeworkRepository,
        user_repo: UserRepository,
    ):
        self.dispatcher = dispatcher
        self.homework_repo = homework_repo
        self.user_repo = user_repo

    async def handle(self, event: HomeworkGraded) -> None:
        """Thông báo cho user kết quả chấm bài của họ."""
        try:
            logger.info(
                f"Handling HomeworkGraded for user {event.user_id}, homework {event.homework_id}"
            )
            homework = self.homework_repo.get_by_id(event.homework_id)
            user = self.user_repo.get_by_id(event.user_id)

            if not homework or not user:
                logger.error(
                    f"Cannot find user {event.user_id} or homework {event.homework_id}"
                )
                return

            asyncio.create_task(self._send_notifications_task(homework, user, event))
            logger.info(
                f"Grading notifications for homework {event.homework_id} for user {event.user_id} scheduled."
            )

        except Exception as e:
            logger.error(f"Error in HomeworkGradedNotificationHandler: {e}")

    async def _send_notifications_task(
        self, homework, user, event: HomeworkGraded
    ) -> None:
        try:
            pass_text = "ĐẠT ✅" if event.is_pass else "KHÔNG ĐẠT ❌"
            score_text = f"{event.score}/10" if event.score is not None else "0/10"
            plagiarized_text = "CÓ ⚠️" if event.is_plagiarized else "KHÔNG"

            fields = [
                {"name": "🎯 Điểm số", "value": score_text, "inline": True},
                {"name": "📊 Trạng thái", "value": pass_text, "inline": True},
                {
                    "name": "🕵️ Phát hiện đạo văn",
                    "value": plagiarized_text,
                    "inline": True,
                },
                {
                    "name": "📋 Lời phê chi tiết",
                    "value": "Vui lòng truy cập website (mục Bài tập của tôi) để xem chi tiết lời phê.",
                    "inline": False,
                },
            ]

            payload = NotificationPayload(
                user_id=user.id,
                title="✅ KẾT QUẢ CHẤM BÀI TẬP",
                content=(
                    f"Chào {user.name}!\n"
                    f"Bài tập {homework.title} của bạn đã được chấm xong. Kết quả: {score_text} ({pass_text})."
                ),
                category=NotificationCategory.HOMEWORK,
                level=NotificationLevel.SUCCESS
                if event.is_pass
                else NotificationLevel.WARNING,
                image_asset="meme-lam-viec-2.jpeg",
                fields=fields,
                action_url=f"/homework/{homework.id}",
                task_type="HOMEWORK",
                task_id=homework.id,
            )

            await self.dispatcher.dispatch(payload)
        except Exception as e:
            logger.error(
                f"Unexpected error in background graded notification task: {e}"
            )
