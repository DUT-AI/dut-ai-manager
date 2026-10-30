# Hướng dẫn Lập trình viên: Chuẩn mực Thời gian (Datetime Quickstart)

**Feature**: `028-enterprise-utc-datetime-refactor`

---

## 🎯 4 Quy tắc Vàng về Thời gian trong Dự án

### Quy tắc 1: Lấy giờ hiện tại (Current Time)
Luôn luôn sử dụng hàm chuẩn của thư viện `datetime` với múi giờ `UTC`:
```python
# ✅ ĐÚNG:
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# ❌ TUYỆT ĐỐI CẤM:
now = datetime.now()             # Bị Ruff Linter chặn
now = datetime.utcnow()          # Bị Deprecated và Linter chặn
now = get_current_utc7_time()    # Đã bị loại bỏ hoàn toàn
```

---

### Quy tắc 2: Định nghĩa trường thời gian trong DTO (Input từ Client)
Sử dụng type `UtcDateTime` để tự động chuyển đổi chuỗi bất kỳ từ Client về UTC:
```python
# ✅ ĐÚNG:
from pydantic import BaseModel
from app.shared.domain.datetime_types import UtcDateTime

class CreateHomeworkDto(BaseModel):
    title: str
    deadline: UtcDateTime  # Tự động hỗ trợ cả chuỗi ISO lẫn chuỗi naive giờ VN
```

---

### Quy tắc 3: Định nghĩa cột trong SQLAlchemy ORM Model
Luôn bật `timezone=True`:
```python
# ✅ ĐÚNG:
from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column

class MeetingModel(Base, SQLAlchemyTimestampMixin):
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

---

### Quy tắc 4: Khi cần tính mốc "Ngày hôm nay tại Việt Nam"
Khi nghiệp vụ yêu cầu biết hôm nay là ngày mấy ở Việt Nam (để thống kê điểm danh, gửi báo cáo hàng ngày):
```python
# ✅ ĐÚNG:
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Lấy ngày theo lịch Việt Nam
today_vn = datetime.now(timezone.utc).astimezone(VN_TZ).date()
```
