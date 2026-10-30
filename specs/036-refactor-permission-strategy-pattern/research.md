# Phase 0: Research & Decision Log

## Decision: Áp dụng Strategy Pattern / Handlers cho Permission Request Category
- **Vấn đề**: `CreatePermissionRequestUseCase` và `DeletePermissionRequestUseCase` đang chứa hàng loạt `if-else` kiểm tra loại đơn (`POSTPONE`, `LATE`, `ABSENCE`) và kéo theo các repository khác nhau (`HomeworkRepository`, `MeetingRepository`). Mỗi khi có loại đơn mới thì phải sửa trực tiếp use case và entity.
- **Mô hình giải pháp**:
  - Tách logic xử lý riêng của từng loại đơn thành **Strategy Handlers**.
  - `PermissionHandlerRegistry` quản lý danh sách các Handler theo `RequestCategory`.
  - Use case chỉ đóng vai trò Orchestrator:
    1. Nhận input $\rightarrow$ Tạo `PermissionRequest` entity.
    2. Lấy handler từ registry $\rightarrow$ `handler.validate(request)`.
    3. Lưu entity qua `repo.save(request)`.
    4. Gọi side-effects $\rightarrow$ `handler.on_created(saved, user_id)`.
    5. Phát event qua `event_bus`.
  - Tương tự khi xóa đơn:
    1. `handler = registry.get(entity.category)`.
    2. `handler.on_deleted(entity, user_id)`.
    3. `repo.delete(request_id)`.
- **Lợi ích**:
  - **Tuân thủ Open/Closed Principle (OCP)**: Thêm loại đơn mới chỉ cần thêm 1 file handler mới mà không động chạm đến mã nguồn cốt lõi của use cases.
  - **Giảm coupling**: `CreatePermissionRequestUseCase` không cần biết đến `MeetingRepository` hay `HomeworkRepository`.
  - **Dễ dàng Unit Test**: Từng Handler có thể test độc lập với các mock tối thiểu.
