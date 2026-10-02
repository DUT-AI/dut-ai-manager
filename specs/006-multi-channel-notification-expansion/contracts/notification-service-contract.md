# Service Contract: Unified Notification Dispatcher

**Feature**: `006-multi-channel-notification-expansion`
**Date**: 2026-10-02

## 1. Dịch Vụ `NotificationService` (Interface & Contract)

Nằm tại `app/shared/infrastructure/notification_service.py`:

```python
from typing import Protocol
from app.shared.infrastructure.notification_payload import NotificationPayload


class NotificationService(Protocol):
    """Giao diện dịch vụ phân phối thông báo đa kênh (Discord + Zalo)."""

    async def send_to_user(self, payload: NotificationPayload) -> dict[str, bool]:
        """
        Gửi thông báo song song đến tất cả các kênh (Discord, Zalo) đã liên kết của người dùng.
        
        Args:
            payload: Cấu trúc thông điệp (chứa user_id, tiêu đề, nội dung, ảnh asset meme, action link, ...)
            
        Returns:
            dict mapping kênh -> trạng thái gửi thành công (e.g. {"discord": True, "zalo": True})
        """
        ...

    async def send_to_room(
        self,
        room_id: str,
        payload: NotificationPayload,
        channel: str = "discord"
    ) -> bool:
        """
        Gửi thông báo vào kênh/room chung (dành cho Admin / Quản lý).
        """
        ...
```

---

## 2. API Contract: Static Assets Serving

FastAPI cung cấp endpoint phục vụ hình ảnh tĩnh từ thư mục assets:

- **Endpoint**: `GET /static/assets/{filename}`
- **Response**: Trả về tệp hình ảnh (`image/webp`, `image/jpeg`, `image/png`).
- **Cache-Control**: `public, max-age=86400`
- **Ví dụ**:
  - `GET https://api.dut-ai-club.com/static/assets/meme-hoc-bai.webp`
  - `GET https://api.dut-ai-club.com/static/assets/meme-xin-tien.jpeg`
  - `GET https://api.dut-ai-club.com/static/assets/meme-doi-no-2.jpg`

---

## 3. Formatting Contract Cho Từng Nền Tảng

### 3.1 Discord Message Contract (Rich Embed)
- **Title**: `{EMOJI} {TITLE}` (ví dụ: `💰 HÓA ĐƠN MỚI CẦN THANH TOÁN`)
- **Description**: Nội dung mô tả chi tiết, hỗ trợ định dạng Markdown (in đậm, ngắt dòng, trích dẫn).
- **Color**: Ánh xạ mã màu HEX theo `NotificationLevel` hoặc danh mục sự kiện.
- **Image**: Link URL tuyệt đối của ảnh meme (`get_asset_url(payload.image_asset)`).
- **Fields**: Danh sách cặp Key-Value (ví dụ: Số tiền, Hạn chót, Mã chuyển khoản).
- **Footer**: `DUT AI Club Manager • UTC+7`

### 3.2 Zalo Bot Message Contract
- **Text format**:
  ```text
  {EMOJI} {TITLE}
  
  {CONTENT}
  
  👉 Chi tiết: {ACTION_URL}
  ```
- **Media**: Sử dụng `send_photo` (hoặc gửi ảnh trực tiếp kèm caption nếu bot hỗ trợ) hoặc tin nhắn văn bản trích dẫn URL ảnh khi photo mode không khả dụng.
