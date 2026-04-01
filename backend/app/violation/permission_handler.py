from app.permission_request.domain.events import PermissionRequestCreated
from app.permission_request.domain.value_objects import RequestCategory
from app.shared.domain.event_bus import EventBus
from app.utils.datetime import get_current_utc7_time
from app.violation.application.use_cases import CreateViolationUseCase
from loguru import logger


class PermissionViolationHandler:
    """Lắng nghe yêu cầu xin phép để tự động tạo vi phạm nếu vượt quá giới hạn"""

    def __init__(self, create_violation_uc: CreateViolationUseCase, permission_repo):
        self.create_violation_uc = create_violation_uc
        self.permission_repo = permission_repo

    async def handle_created(self, event: PermissionRequestCreated):
        """Xử lý khi có yêu cầu xin phép mới được tạo"""
        if event.category not in [RequestCategory.ABSENCE, RequestCategory.POSTPONE]:
            return

        month = event.date.month
        year = event.date.year

        # Đếm số lượng yêu cầu TRƯỚC ĐÓ trong tháng (không tính yêu cầu vừa tạo - id đã có)
        # Tuy nhiên trong logic cũ, nó đếm tất cả bao gồm cả cái vừa tạo.
        # Nếu count >= 2 (nghĩa là cái vừa tạo là cái thứ 2 trở đi) -> Tạo vi phạm.

        count = self.permission_repo.count_by_user_category_month(
            user_id=event.user_id, category=event.category, month=month, year=year
        )

        if count >= 2:
            category_text = (
                "xin vắng sinh hoạt"
                if event.category == RequestCategory.ABSENCE
                else "xin tạm hoãn bài tập"
            )
            reason = (
                f"{category_text.capitalize()} lần {count} trong tháng {month}/{year}"
            )

            logger.info(f"Tự động tạo vi phạm cho user {event.user_id}: {reason}")

            await self.create_violation_uc.execute(
                user_ids=[event.user_id],
                reason=reason,
                date=get_current_utc7_time(),
                is_system=True,
                system_user_id=0,  # System ID
            )


def register_permission_handlers(
    event_bus: type[EventBus], handler: PermissionViolationHandler
):
    """Đăng ký các hàm xử lý sự kiện với EventBus"""
    event_bus.subscribe(PermissionRequestCreated, handler.handle_created)
