# Data Model: Nâng Cấp Hệ Thống Thông Báo Đa Kênh & Tích Hợp Assets Meme

**Feature**: `006-multi-channel-notification-expansion`
**Date**: 2026-10-02

## 1. Domain Entities & Value Objects

### 1.1 NotificationPayload (Value Object)
Đối tượng truyền tải dữ liệu thông báo chuẩn hóa xuyên suốt hệ thống:

```python
from dataclasses import dataclass
from enum import Enum


class NotificationCategory(str, Enum):
    BILLING = "billing"
    HOMEWORK = "homework"
    VIOLATION = "violation"
    BONUS_POINT = "bonus_point"
    MEETING = "meeting"
    PERMISSION_REQUEST = "permission_request"


class NotificationLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True)
class NotificationPayload:
    user_id: int
    title: str
    content: str
    category: NotificationCategory
    level: NotificationLevel = NotificationLevel.INFO
    image_asset: str | None = None  # Tên file trong app/assets (ví dụ: 'meme-hoc-bai.webp')
    image_url: str | None = None    # URL ảnh tùy chỉnh bên ngoài
    action_url: str | None = None   # Link điều hướng (Frontend URL)
    fields: list[dict[str, str]] | None = None  # Các cặp key-value hiển thị trên Embed/Card
    color_hex: int | None = None    # Màu viền Discord Embed
```

---

## 2. Domain Events (Bổ Sung Mới)

### 2.1 Billing Domain Events (`app/billing/domain/events.py`)

```python
from dataclasses import dataclass
from datetime import date, datetime
from app.shared.domain.event_bus import DomainEvent


@dataclass(frozen=True)
class InvoiceCreated(DomainEvent):
    invoice_id: int
    user_id: int
    amount: int
    reference_code: str
    description: str | None
    billing_period: date
    occurred_at: datetime = None


@dataclass(frozen=True)
class InvoicePaid(DomainEvent):
    invoice_id: int
    user_id: int
    amount: int
    reference_code: str
    transaction_id: str
    paid_at: datetime
    occurred_at: datetime = None
```

---

## 3. Database Schema & Models

Hệ thống thông báo hoạt động theo cơ chế **Event-Driven Stateless & Non-blocking**:
- Không yêu cầu thay đổi cấu trúc bảng trong PostgreSQL/SQLite.
- Sử dụng các trường định danh sẵn có trên bảng `users`:
  - `users.discord_id: str | None`
  - `users.zalo_bot_id: str | None`
- Phục vụ ảnh tĩnh thông qua FastAPI static mount từ thư mục `backend/app/assets`.
