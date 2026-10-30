# Data Model & Schema Specification: Enterprise UTC Datetime

**Feature**: `028-enterprise-utc-datetime-refactor`  
**Date**: 2026-10-30  

---

## 1. Danh sách các Bảng & Cột cần Chuyển đổi sang `TIMESTAMPTZ`

Tất cả các cột `DateTime` trong hệ thống sẽ được chuyển đổi sang kiểu dữ liệu `TIMESTAMPTZ` (`DateTime(timezone=True)`).

| Bảng (Table) | Cột Thời gian (Columns) | Kiểu Cũ | Kiểu Mới | Ghi chú |
| :--- | :--- | :--- | :--- | :--- |
| **All Tables** (kế thừa `SQLAlchemyTimestampMixin`) | `created_at`, `updated_at` | `TIMESTAMP` | `TIMESTAMPTZ` | Timestamp kiểm toán tự động |
| **meetings** | `start_time`, `end_time` | `TIMESTAMP` | `TIMESTAMPTZ` | Thời gian bắt đầu / kết thúc cuộc họp |
| **meeting_participants** | `check_in_time`, `check_out_time` | `TIMESTAMP` | `TIMESTAMPTZ` | Thời điểm điểm danh / check-out |
| **homeworks** | `deadline` | `TIMESTAMP` | `TIMESTAMPTZ` | Hạn nộp bài tập |
| **homework_submissions** | `submitted_at` | `TIMESTAMP` | `TIMESTAMPTZ` | Thời điểm nộp bài |
| **bonus_points** | `date` | `DATE` / `TIMESTAMP` | Giữ `DATE` nếu là ngày thuần túy, `TIMESTAMPTZ` nếu có giờ | Điểm cộng |
| **cleaning_duties** | `submitted_at`, `approved_at`, `rejected_at` | `TIMESTAMP` | `TIMESTAMPTZ` | Thời điểm nộp minh chứng / duyệt trực nhật |
| **permission_requests** | `start_time`, `end_time` | `TIMESTAMP` | `TIMESTAMPTZ` | Thời gian xin phép nghỉ/đổi ca |
| **notifications** | `read_at` | `TIMESTAMP` | `TIMESTAMPTZ` | Thời điểm đọc thông báo |
| **violations** | `date` | `DATE` / `TIMESTAMP` | `TIMESTAMPTZ` | Thời điểm ghi nhận vi phạm |

---

## 2. Base Model & Mixin (`backend/app/shared/infrastructure/base_model.py`)

```python
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class SQLAlchemyTimestampMixin:
    """Mixin cung cấp created_at, updated_at chuẩn UTC tuyệt đối."""
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=True
    )
```

---

## 3. Schema DTO & Type Definition (`backend/app/shared/domain/datetime_types.py`)

```python
from datetime import datetime, timezone
from typing import Annotated, Any
from zoneinfo import ZoneInfo
from pydantic import BeforeValidator, PlainSerializer

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def parse_to_utc(val: Any) -> datetime | None:
    """Parser chuẩn hóa mọi input thời gian từ Client về UTC aware."""
    if val is None or val == "":
        return None
    
    if isinstance(val, str):
        val = val.strip()
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
    elif isinstance(val, datetime):
        dt = val
    else:
        raise ValueError(f"Không thể parse {val} sang datetime")

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)

    return dt.astimezone(timezone.utc)

def serialize_to_iso(dt: datetime | None) -> str | None:
    """Serializer xuất ra ISO 8601 kèm Z hoặc offset cho Client."""
    if dt is None:
        return None
    return dt.isoformat()

# Dùng cho Request DTO (Ingestion)
UtcDateTime = Annotated[datetime, BeforeValidator(parse_to_utc)]

# Dùng cho Response DTO (Serialization)
IsoDateTime = Annotated[datetime, PlainSerializer(serialize_to_iso, return_type=str)]
```
