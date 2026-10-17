# Nghiên cứu Kỹ thuật: Phân rã Use Cases Miền Điểm Thưởng (Research)

**Feature**: `011-bonus-point-modular-use-cases`
**Date**: 2026-10-17

## 1. Hiện trạng & Phân tích Vấn đề

Tệp `backend/app/bonus_point/application/use_cases.py` hiện đang chứa 6 use case khác nhau trong một tệp duy nhất (246 dòng mã):
1. `GetBonusPointsUseCase`: Truy vấn danh sách điểm thưởng với bộ lọc (user_id, type, date range, pagination).
2. `CreateBonusPointsUseCase`: Tạo bản ghi điểm thưởng cho một hoặc nhiều người dùng và phát sự kiện miền `BonusPointCreated`.
3. `UpdateBonusPointUseCase`: Cập nhật lý do, điểm, loại điểm và phát sự kiện miền `BonusPointUpdated`.
4. `DeleteBonusPointUseCase`: Xóa mềm điểm thưởng và phát sự kiện `BonusPointDeleted`.
5. `RestoreBonusPointUseCase`: Phục hồi bản ghi điểm thưởng đã xóa.
6. `CalculateActivityPointsUseCase`: Tiến trình nghiệp vụ tính điểm thưởng dựa trên thời gian tham gia sinh hoạt CLB (từ dữ liệu điểm danh của Participant).

### Vi phạm Kiến trúc:
- **Constitution Principle VII**: "Each use case in the `application/` layer of every domain MUST be implemented in its own dedicated Python file with the `*_use_case.py` naming convention... Grouping multiple use case classes into a monolithic file (such as `use_cases.py`) is prohibited. The `application/__init__.py` file MUST explicitly re-export all domain use cases via `__all__`."

---

## 2. Quyết định Kỹ thuật (Technical Decisions)

### Quyết định 1: Phân tách tệp theo tỷ lệ 1-1
- **Quyết định**: Mỗi use case được đưa vào một tệp riêng biệt theo đúng quy ước `*_use_case.py`:
  - `GetBonusPointsUseCase` -> `get_bonus_points_use_case.py`
  - `CreateBonusPointsUseCase` -> `create_bonus_points_use_case.py`
  - `UpdateBonusPointUseCase` -> `update_bonus_point_use_case.py`
  - `DeleteBonusPointUseCase` -> `delete_bonus_point_use_case.py`
  - `RestoreBonusPointUseCase` -> `restore_bonus_point_use_case.py`
  - `CalculateActivityPointsUseCase` -> `calculate_activity_points_use_case.py`

### Quyết định 2: Xóa hoàn toàn tệp `use_cases.py` (Không dùng Shim)
- **Quyết định**: Xóa thẳng tệp `use_cases.py` sau khi hoàn tất di chuyển.
- **Lý do**:
  - Khảo sát thực tế toàn bộ repository: Chỉ có chính xác **3 vị trí** import `app.bonus_point.application.use_cases` (`providers.py`, `controller.py`, `activity_scoring_job.py`).
  - Không có bất kỳ test suite nào phụ thuộc vào đường dẫn tệp cũ.
  - Việc xóa hoàn toàn giúp loại bỏ 100% nợ kỹ thuật (technical debt), mã nguồn hoàn toàn sạch sẽ và minh bạch.

### Quyết định 3: Xuất khẩu chuẩn qua `__init__.py` và cập nhật các điểm gọi
- **Quyết định**:
  - `app/bonus_point/application/__init__.py` re-export cả 6 use case và khai báo trong `__all__`.
  - Cập nhật import trong `providers.py`, `controller.py` và `activity_scoring_job.py` thành:
    ```python
    from app.bonus_point.application import (
        CalculateActivityPointsUseCase,
        CreateBonusPointsUseCase,
        DeleteBonusPointUseCase,
        GetBonusPointsUseCase,
        RestoreBonusPointUseCase,
        UpdateBonusPointUseCase,
    )
    ```
