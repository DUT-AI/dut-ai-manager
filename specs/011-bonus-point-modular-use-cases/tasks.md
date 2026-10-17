# Tasks: Tách Biệt Use Cases Đơn Nhiệm Miền Điểm Thưởng (Bonus Point Modular Use Cases)

**Feature**: `011-bonus-point-modular-use-cases`  
**Date**: 2026-10-17  
**Status**: Completed  

---

## Danh Sách Nhiệm Vụ (Task Checklist)

### Phase 1: Trích xuất các tệp Use Case Đơn Nhiệm
- [x] **TASK-001**: Tạo [get_bonus_points_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/get_bonus_points_use_case.py) chứa `GetBonusPointsUseCase`.
- [x] **TASK-002**: Tạo [create_bonus_points_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/create_bonus_points_use_case.py) chứa `CreateBonusPointsUseCase`.
- [x] **TASK-003**: Tạo [update_bonus_point_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/update_bonus_point_use_case.py) chứa `UpdateBonusPointUseCase`.
- [x] **TASK-004**: Tạo [delete_bonus_point_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/delete_bonus_point_use_case.py) chứa `DeleteBonusPointUseCase`.
- [x] **TASK-005**: Tạo [restore_bonus_point_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/restore_bonus_point_use_case.py) chứa `RestoreBonusPointUseCase`.
- [x] **TASK-006**: Tạo [calculate_activity_points_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/calculate_activity_points_use_case.py) chứa `CalculateActivityPointsUseCase`.

### Phase 2: Cấu hình Gói Ứng dụng & Re-export
- [x] **TASK-007**: Cập nhật [__init__.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/application/__init__.py) xuất khẩu cả 6 use case qua danh sách `__all__` đầy đủ theo Constitution Principle VII.

### Phase 3: Chuẩn hóa Điểm Gọi & Xóa Tệp Nguyên Khối Cũ
- [x] **TASK-008**: Cập nhật import trong [providers.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/providers.py) sang `from app.bonus_point.application import (...)`.
- [x] **TASK-009**: Cập nhật import trong [controller.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/bonus_point/controller.py) sang `from app.bonus_point.application import (...)`.
- [x] **TASK-010**: Cập nhật import trong [activity_scoring_job.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/jobs/activity_scoring_job.py) sang `from app.bonus_point.application import CalculateActivityPointsUseCase`.
- [x] **TASK-011**: Xóa bỏ hoàn toàn tệp nguyên khối cũ `backend/app/bonus_point/application/use_cases.py`.

### Phase 4: Kiểm thử & Xác minh Zero Regression
- [x] **TASK-012**: Chạy kiểm tra tĩnh (`grep`) xác nhận không còn bất kỳ dòng tham chiếu nào tới `app.bonus_point.application.use_cases` trong mã nguồn.
- [x] **TASK-013**: Chạy test suites `backend/tests/api/test_bonus_point_api.py`, `backend/tests/unit/test_billing_use_cases.py`, `backend/tests/api/test_report_api.py` (26/26 tests passed).
