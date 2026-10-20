"""
Notification Controller.
REST API endpoints for member notifications.
"""

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Query, status

from app.core.deps import CurrentUser
from app.reminder.application.dtos import (
    NotificationDto,
    TriggerReminderScanResponseDto,
    UnreadCountDto,
)
from app.reminder.application.get_my_notifications_use_case import (
    GetMyNotificationsUseCase,
)
from app.reminder.application.get_unread_notification_count_use_case import (
    GetUnreadNotificationCountUseCase,
)
from app.reminder.application.mark_all_notifications_as_read_use_case import (
    MarkAllNotificationsAsReadUseCase,
)
from app.reminder.application.mark_notification_as_read_use_case import (
    MarkNotificationAsReadUseCase,
)
from app.reminder.application.scan_and_send_reminders_use_case import (
    ScanAndSendRemindersUseCase,
)
from app.reminder.domain.entity import NotificationCategory
from app.shared.application.response import ApiResponse, PaginationMeta

router = APIRouter(
    prefix="/notifications",
    tags=["Notifications"],
    route_class=DishkaRoute,
)


@router.post("/trigger", response_model=ApiResponse[TriggerReminderScanResponseDto])
async def trigger_reminder_scan(
    current_user: CurrentUser,
    use_case: FromDishka[ScanAndSendRemindersUseCase],
    dry_run: bool = False,
):
    """Kích hoạt quét và gửi nhắc việc thủ công (Admin)."""
    res = await use_case.execute(dry_run=dry_run)
    return ApiResponse.success(data=res, message="Quét và gửi nhắc nhở thành công")


@router.get("/my", response_model=ApiResponse[list[NotificationDto]])
async def get_my_notifications(
    current_user: CurrentUser,
    use_case: FromDishka[GetMyNotificationsUseCase],
    category: NotificationCategory | None = None,
    is_read: bool | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """Lấy danh sách thông báo của tôi (hỗ trợ phân trang và lọc)."""
    items, total = await use_case.execute(
        user_id=current_user.user_id,
        category=category,
        is_read=is_read,
        page=page,
        page_size=page_size,
    )
    pagination = PaginationMeta.create(page=page, page_size=page_size, total=total)
    return ApiResponse.success(
        data=items,
        pagination=pagination,
        message="Lấy danh sách thông báo thành công",
    )


@router.get("/unread-count", response_model=ApiResponse[UnreadCountDto])
async def get_unread_count(
    current_user: CurrentUser,
    use_case: FromDishka[GetUnreadNotificationCountUseCase],
):
    """Đếm số lượng thông báo chưa đọc của tôi."""
    res = await use_case.execute(user_id=current_user.user_id)
    return ApiResponse.success(data=res, message="Lấy số thông báo chưa đọc thành công")


@router.patch("/{id}/read", response_model=ApiResponse[NotificationDto | None])
async def mark_as_read(
    id: int,
    current_user: CurrentUser,
    use_case: FromDishka[MarkNotificationAsReadUseCase],
):
    """Đánh dấu một thông báo là đã đọc."""
    item = await use_case.execute(notification_id=id, user_id=current_user.user_id)
    return ApiResponse.success(data=item, message="Đánh dấu đã đọc thành công")


@router.post("/read-all", response_model=ApiResponse[int])
async def mark_all_as_read(
    current_user: CurrentUser,
    use_case: FromDishka[MarkAllNotificationsAsReadUseCase],
):
    """Đánh dấu tất cả thông báo của tôi là đã đọc."""
    count = await use_case.execute(user_id=current_user.user_id)
    return ApiResponse.success(data=count, message=f"Đã đánh dấu {count} thông báo là đã đọc")
