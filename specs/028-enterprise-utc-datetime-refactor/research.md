# Nghiên cứu Kỹ thuật: Chuẩn hóa Kiến trúc Thời gian UTC (Enterprise UTC Datetime)

**Feature**: `028-enterprise-utc-datetime-refactor`  
**Date**: 2026-10-30  

---

## 1. Nghiên cứu Tầng Cơ sở Dữ liệu (PostgreSQL & SQLAlchemy)

### 1.1 Sự khác biệt giữa `TIMESTAMP` và `TIMESTAMPTZ` trong PostgreSQL
- `TIMESTAMP` (`WITHOUT TIME ZONE`): Chỉ lưu các con số ngày-tháng-năm giờ-phút-giây nguyên bản. Database không hề biết con số đó thuộc múi giờ nào.
- `TIMESTAMPTZ` (`WITH TIME ZONE`): PostgreSQL chuyển đổi bất kỳ thời điểm nào thành **UTC tuyệt đối** và lưu trữ 8 bytes dưới dạng microsecond epoch. Khi truy vấn ra, nó sẽ trả về mốc thời gian kèm múi giờ.

### 1.2 Chiến lược Chuyển đổi Dữ liệu Lịch sử An toàn (Data Migration Strategy)
Dữ liệu hiện tại trong DB đang là naive timestamp của giờ Việt Nam (ví dụ: `2026-10-25 19:30:00`).
Nếu chỉ chạy `ALTER TABLE ... TYPE TIMESTAMPTZ`, PostgreSQL sẽ hiểu nhầm giá trị đó theo timezone hiện tại của session (thường là UTC), dẫn đến giá trị bị sai lệch 7 tiếng.

**Giải pháp chuẩn xác trong Alembic**:
Sử dụng mệnh đề `AT TIME ZONE 'Asia/Ho_Chi_Minh'` để chỉ định rõ ràng cho PostgreSQL:
```sql
ALTER TABLE meetings 
ALTER COLUMN start_time TYPE TIMESTAMPTZ 
USING start_time AT TIME ZONE 'Asia/Ho_Chi_Minh';
```
*Kết quả*: Con số `19:30:00` sẽ được dịch chuyển chuẩn xác thành `12:30:00+00` (UTC).

### 1.3 Cấu hình SQLAlchemy 2.0 ORM
Tại `backend/app/shared/infrastructure/base_model.py`:
```python
from datetime import datetime, timezone
from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

class SQLAlchemyTimestampMixin:
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
```

---

## 2. Nghiên cứu Tầng Ingestion & Deserialization (Pydantic V2)

### 2.1 Thách thức
Frontend hiện tại gửi lên chuỗi `YYYY-MM-DDTHH:mm:ss` (không kèm offset):
`"2026-10-31T19:30:00"`

### 2.2 Giải pháp Custom Pydantic Type `UtcDateTime`
Áp dụng nguyên lý *Robustness Principle*: Chấp nhận cả chuỗi có múi giờ và chuỗi thiếu múi giờ.

```python
from datetime import datetime, timezone
from typing import Annotated, Any
from zoneinfo import ZoneInfo
from pydantic import BeforeValidator

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

def parse_to_utc(val: Any) -> datetime | None:
    if val is None or val == "":
        return None
    
    if isinstance(val, str):
        # Parse ISO string
        dt = datetime.fromisoformat(val.replace("Z", "+00:00"))
    elif isinstance(val, datetime):
        dt = val
    else:
        raise ValueError(f"Cannot parse {val} to datetime")

    # Nếu chuỗi không chứa thông tin múi giờ (naive) -> Mặc định gán là giờ Việt Nam
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=VN_TZ)

    # Chuyển đổi về múi giờ chuẩn UTC
    return dt.astimezone(timezone.utc)

UtcDateTime = Annotated[datetime, BeforeValidator(parse_to_utc)]
```

---

## 3. Nghiên cứu Tầng Domain & Use Cases

### 3.1 Thay thế toàn bộ Call Sites của `get_current_utc7_time`
Tất cả các use-case cần lấy thời điểm hiện tại sẽ thay thế:
```python
# CŨ:
from app.utils.datetime import get_current_utc7_time
now = get_current_utc7_time()

# MỚI (Chuẩn Python 3.11+):
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

### 3.2 So sánh ngày nghiệp vụ (Date Boundaries)
Với các nghiệp vụ so sánh theo "ngày" (ví dụ: quét bài tập trong ngày hôm nay ở Việt Nam):
```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")
now_vn = datetime.now(timezone.utc).astimezone(VN_TZ)
today_vn = now_vn.date()
```

---

## 4. Nghiên cứu Cơ chế Linter Enforce (Ruff `DTZ`)

Trong file `backend/pyproject.toml`:
```toml
[tool.ruff.lint]
select = [
    # ...,
    "DTZ",  # flake8-datetimez
]
```
Các rule được kích hoạt:
- `DTZ001`: Cấm `datetime.datetime()` không có `tzinfo`.
- `DTZ005`: Cấm `datetime.datetime.now()` không có `tz`.
- `DTZ003`: Cấm `datetime.datetime.utcnow()` (đã bị deprecate).

Điều này đảm bảo vĩnh viễn không một lập trình viên nào có thể commit code sử dụng datetime không múi giờ vào dự án.
