# Hướng dẫn Kiểm thử & Vận hành: Điểm Thưởng Đơn Nhiệm (Quickstart)

**Feature**: `011-bonus-point-modular-use-cases`
**Date**: 2026-10-17

Hướng dẫn xác thực sau khi hoàn thành việc tách các tệp use case của miền điểm thưởng.

---

## 1. Kiểm thử Tự động (Automated Tests)

Chạy các bài kiểm thử liên quan trực tiếp đến use case và API điểm thưởng:

```bash
# 1. Chạy test suite use cases liên quan đến billing & bonus points
backend/.venv/bin/pytest backend/tests/unit/test_billing_use_cases.py -v

# 2. Chạy test suite API của bonus point
backend/.venv/bin/pytest backend/tests/api/test_bonus_point_api.py -v

# 3. Chạy kiểm thử job tính điểm hoạt động CLB
backend/.venv/bin/pytest backend/tests/api/test_report_api.py -v
```

**Kỳ vọng**:
- Toàn bộ các test cases đều đạt trạng thái `PASSED`.
- Không phát sinh lỗi `ImportError` hoặc lỗi inject trong Dishka.

---

## 2. Kiểm thử Xuất nhập khẩu Trực tiếp & Xác nhận Xóa File (Direct Import & File Check)

Chạy kiểm tra import trực tiếp từ `app.bonus_point.application` và đảm bảo `use_cases.py` đã bị xóa:

```bash
# Xác nhận use_cases.py không còn tồn tại
test ! -f backend/app/bonus_point/application/use_cases.py && echo "use_cases.py successfully removed!"

# Xác nhận import trực tiếp từ application package
backend/.venv/bin/python3 -c "
from app.bonus_point.application import (
    GetBonusPointsUseCase,
    CreateBonusPointsUseCase,
    UpdateBonusPointUseCase,
    DeleteBonusPointUseCase,
    RestoreBonusPointUseCase,
    CalculateActivityPointsUseCase,
)
print('All 6 use cases imported directly from app.bonus_point.application successfully!')
"
```
