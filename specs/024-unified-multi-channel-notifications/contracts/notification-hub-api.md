# Contract: Unified Notification Hub API & Service Interfaces

**Feature**: `024-unified-multi-channel-notifications`
**Date**: 2026-10-22
**Status**: Ready for Implementation

## 1. Core Internal Dispatcher Interface

Interface mà tất cả các Use Case và Event Handler trong toàn bộ hệ thống gọi để phát thông báo.

### `UnifiedNotificationDispatcher`

```python
class UnifiedNotificationDispatcher:
    """
    Cổng điều phối phát thông báo trung tâm cho toàn bộ hệ thống DUT AI Manager.
    Tự động:
    1. Lưu thông báo nội bộ vào In-App DB (notifications table).
    2. Chạy ngầm phân phối đa kênh (Discord, Zalo, Web Push) với Fault Isolation và Retry.
    """
    async def dispatch(self, payload: NotificationPayload) -> Notification:
        """
        Phát một thông báo cá nhân đến người dùng qua tất cả các kênh được kích hoạt.
        Trả về entity Notification vừa được tạo và lưu vào In-App DB.
        """
        ...

    async def dispatch_room(
        self,
        room_id: str,
        title: str,
        content: str,
        level: NotificationLevel = NotificationLevel.INFO,
        image_asset: str | None = None,
        fields: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Phát thông báo vào một Room / Kênh quản trị chung (ví dụ Discord Admin Room).
        """
        ...
```

---

## 2. Notification Channel Adapter Interface

Interface cho các Adapter kênh gửi tin tuân thủ Strategy Pattern (Open-Closed Principle):

```python
class NotificationChannel(Protocol):
    """Protocol chuẩn hóa cho mọi kênh gửi thông báo."""
    
    @property
    def channel_type(self) -> ChannelType:
        """Tên định danh kênh (DISCORD, ZALO, WEB_PUSH)."""
        ...

    async def send(self, user: User, payload: NotificationPayload) -> ChannelDeliveryResult:
        """
        Thực hiện gửi thông báo đến người dùng qua kênh này.
        Trả về ChannelDeliveryResult (status: SENT, FAILED, NO_ACCOUNT, BLOCKED; error_message: str | None).
        Không bao giờ quăng ngoại lệ ra ngoài (phải tự catch và đóng gói kết quả).
        """
        ...
```

---

## 3. REST API Contract (Endpoints cho Web Frontend & Zalo Mini App)

Các endpoints được phục vụ tại `/api/v1/notifications` (hoặc `/notifications`).

### `GET /notifications/my`
Lấy danh sách thông báo của người dùng hiện tại (hỗ trợ phân trang và lọc).

- **Headers**: `Authorization: Bearer <token>`
- **Query Parameters**:
  - `category`: `NotificationCategory` (optional)
  - `is_read`: `boolean` (optional)
  - `page`: `int` (default: 1, min: 1)
  - `page_size`: `int` (default: 20, min: 1, max: 100)
- **Response**: `ApiResponse[list[NotificationDto]]`
```json
{
  "success": true,
  "data": [
    {
      "id": 105,
      "user_id": 12,
      "title": "📚 BÀI TẬP VỀ NHÀ MỚI",
      "content": "Bạn vừa được giao bài tập: Xây dựng Classifier. Hạn nộp: 23:59 25/10/2026.",
      "category": "HOMEWORK",
      "level": "INFO",
      "action_url": "/homework/15",
      "image_url": "/assets/meme-hoc-bai.webp",
      "is_read": false,
      "read_at": null,
      "created_at": "2026-10-22T08:30:00+07:00"
    }
  ],
  "meta": {
    "page": 1,
    "page_size": 20,
    "total_items": 1,
    "total_pages": 1
  },
  "message": "Lấy danh sách thông báo thành công"
}
```

### `GET /notifications/unread-count`
Lấy số lượng thông báo chưa đọc của người dùng để hiển thị huy hiệu (badge).

- **Headers**: `Authorization: Bearer <token>`
- **Response**: `ApiResponse[UnreadCountDto]`
```json
{
  "success": true,
  "data": {
    "unread_count": 3
  },
  "message": "Lấy số lượng thông báo chưa đọc thành công"
}
```

### `PATCH /notifications/{notification_id}/read`
Đánh dấu một thông báo cụ thể là đã đọc.

- **Headers**: `Authorization: Bearer <token>`
- **Response**: `ApiResponse[NotificationDto]`
```json
{
  "success": true,
  "data": {
    "id": 105,
    "is_read": true,
    "read_at": "2026-10-22T08:35:12+07:00"
  },
  "message": "Đã đánh dấu thông báo là đã đọc"
}
```

### `POST /notifications/read-all`
Đánh dấu tất cả thông báo của người dùng hiện tại là đã đọc.

- **Headers**: `Authorization: Bearer <token>`
- **Response**: `ApiResponse[ReadAllNotificationsResponseDto]`
```json
{
  "success": true,
  "data": {
    "updated_count": 3
  },
  "message": "Đã đánh dấu tất cả thông báo là đã đọc"
}
```
