# Implementation Plan: Lược bỏ is_deleted trên các Model không cần thiết (Prune Unneeded Soft Delete)

**Branch**: `060-prune-unneeded-soft-delete` | **Date**: 2026-11-11 | **Spec**: [specs/060-prune-unneeded-soft-delete/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/060-prune-unneeded-soft-delete/spec.md)

**Input**: Feature specification from `specs/060-prune-unneeded-soft-delete/spec.md`

## Summary
Lược bỏ cờ xóa mềm `is_deleted` trên các bảng và model không yêu cầu lưu trữ lịch sử hoặc có xung đột nghiệp vụ khi xóa mềm: `meetings`, `meeting_participants`, `homeworks`, `homework_assignees`, `team_members`, `user_roles`, `notifications`, `push_subscriptions`, `permissions`, `roles`, `teams`, `monthly_user_stats`, `invoice_items`, `cleaning_duties`. Chuyển đổi toàn diện sang cơ chế Hard Delete vật lý, tối ưu hóa hiệu năng truy vấn, loại bỏ các mệnh đề lọc thừa và dọn dẹp an toàn các bản ghi đã xóa mềm trước đây trong cơ sở dữ liệu.

## Technical Context

**Language/Version**: Python 3.12, FastAPI, SQLAlchemy 2.0 (Mapped / mapped_column)

**Primary Dependencies**: Alembic, Pydantic V2, Dishka, PostgreSQL

**Storage**: PostgreSQL (`dut_ai_manager_prod`, `dut_ai_manager_dev`)

**Testing**: pytest (AnyIO strict mode, unit + api test suites)

**Target Platform**: Linux / macOS server

**Project Type**: Backend Web API Service

**Performance Goals**: Giảm dung lượng bảng và kích thước index, loại bỏ lọc `WHERE is_deleted = false` trên các bảng có lưu lượng truy vấn cao nhất (`meetings`, `meeting_participants`).

**Constraints**:
- Không làm ảnh hưởng đến các bảng bắt buộc giữ soft-delete: `invoices`, `outgoing_invoices`, `violations`, `permission_requests`, `users`, `bonus_points`.
- Dọn dẹp an toàn các bản ghi phụ thuộc theo thứ tự cascade trước khi `DROP COLUMN is_deleted`.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Hiến pháp | Trạng thái | Đánh giá tuân thủ |
| :--- | :---: | :--- |
| **Principle I: Clean Architecture & Practical DDD** | ✅ PASS | Giữ nguyên ranh giới Domain Entity, Repository và ORM Model. Base Repository tự động phát hiện model có hay không có `is_deleted`. |
| **Principle II: Dependency Injection with Dishka** | ✅ PASS | Không can thiệp cấu trúc DI providers. |
| **Principle III: Enterprise UTC Storage** | ✅ PASS | Toàn bộ timestamp `created_at`, `updated_at` tiếp tục tuân thủ `DateTime(timezone=True)`. |
| **Principle X: Zero Redundant Backward Compatibility** | ✅ PASS | Loại bỏ triệt để cột thừa `is_deleted` trên các bảng không cần thiết, chuyển sang Hard Delete trực tiếp. |
| **Principle XIV: No Fake Optionals** | ✅ PASS | Không dùng optional thừa. |

## Project Structure

### Documentation (this feature)

```text
specs/060-prune-unneeded-soft-delete/
├── spec.md              # Đặc tả yêu cầu & khảo sát dữ liệu PROD
├── plan.md              # Kế hoạch thực thi (File này)
├── research.md          # Phân tích rủi ro & phương án kỹ thuật
├── data-model.md        # Mô hình phân loại Mixin & Model
├── quickstart.md        # Hướng dẫn chạy & kiểm thử
└── tasks.md             # Danh sách task chi tiết (/speckit-tasks)
```

## Phases of Execution

### Phase 0: Research & Risk Analysis ✅ (Hoàn thành trong research.md)
- Khảo sát dữ liệu thực tế trên PROD: xác định chính xác số lượng bản ghi `is_deleted = true` cần xử lý.
- Phân tích ràng buộc Foreign Key: đảm bảo cascade xóa sạch bản ghi con khi hard delete.

### Phase 1: Architecture & Model Design ✅ (Hoàn thành trong data-model.md)
- Thiết lập `SQLAlchemyAuditTimestampMixin` cho các entity chỉ cần audit (created_by, updated_by, created_at, updated_at) mà không cần soft-delete.
- Phân loại rõ ràng 2 nhóm Model: Hard-Delete vs Soft-Delete.

### Phase 2: Implementation & Migration (Chờ /speckit-tasks & /speckit-implement)
- Cập nhật các ORM Model sang `SQLAlchemyAuditTimestampMixin` hoặc `SQLAlchemyTimestampOnlyMixin`.
- Cập nhật các Domain Entity tương ứng.
- Rà soát các câu query repository để gỡ bỏ `where(Model.is_deleted.is_(False))` thủ công.
- Tạo file migration Alembic: Dọn dẹp dữ liệu cũ và `DROP COLUMN is_deleted`.
- Kiểm thử toàn diện test suite (`pytest`).
