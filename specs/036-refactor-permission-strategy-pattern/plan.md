# Implementation Plan: Generic Payload Entity & Strategy Pattern

**Branch**: `036-refactor-permission-strategy-pattern` | **Date**: 2026-10-31 | **Spec**: [specs/036-refactor-permission-strategy-pattern/spec.md](spec.md)

## Summary
Triển khai kiến trúc **Generic Entity `PermissionRequest[TPayload]`** kết hợp **Strategy Pattern** và lưu trữ dữ liệu dạng **JSONB Payload** cho module `permission_request`. Loại bỏ hoàn toàn `dict[str, Any]`, đảm bảo tính chặt chẽ về mặt kiểu dữ liệu (Strict Type-Safety), tuân thủ Open/Closed Principle (OCP) và hỗ trợ mở rộng không giới hạn các loại đơn trong tương lai.

## Technical Context
- **Language/Version**: Python 3.12 (TypeVar, Generic, Pydantic V2, SQLAlchemy 2.0).
- **Architecture**: Domain-Driven Design (Generic Entity, Value Objects, Strategy Pattern, JSONB Persistence).
- **Constraints**: 100% Type-Safe (Không có `dict[str, Any]` trong Domain), Zero Downtime / Không làm gãy API Frontend, 168 unit tests pass.

## Implementation Tasks (Atomic Checklist)

### Phase 1: Domain Value Objects & Generic Entity
- [ ] T001 Tạo các Typed Payloads trong `backend/app/permission_request/domain/payloads.py` (`BasePermissionPayload`, `AbsencePayload`, `LatePayload`, `PostponePayload`, `OtherPayload`, `ChangeMeetingPayload`).
- [ ] T002 Cập nhật `backend/app/permission_request/domain/entity.py` thành Generic Entity `PermissionRequest[TPayload]`.

### Phase 2: Strategy Pattern Implementation
- [ ] T003 Tạo base interface `PermissionStrategy[TPayload]` trong `backend/app/permission_request/application/strategies/base.py`.
- [ ] T004 Tạo `AbsenceStrategy` trong `backend/app/permission_request/application/strategies/absence_strategy.py`.
- [ ] T005 Tạo `LateStrategy` trong `backend/app/permission_request/application/strategies/late_strategy.py`.
- [ ] T006 Tạo `PostponeStrategy` trong `backend/app/permission_request/application/strategies/postpone_strategy.py`.
- [ ] T007 Tạo `OtherStrategy` trong `backend/app/permission_request/application/strategies/other_strategy.py`.
- [ ] T008 Tạo `PermissionStrategyRegistry` trong `backend/app/permission_request/application/strategies/registry.py`.
- [ ] T009 Export sạch sẽ các strategies trong `backend/app/permission_request/application/strategies/__init__.py`.

### Phase 3: Storage & Model Refactor (JSONB Payload)
- [ ] T010 Cập nhật ORM Model `backend/app/permission_request/infrastructure/model.py` bổ sung cột `payload: Mapped[dict] = mapped_column(JSONB, default=dict)` và ánh xạ `to_entity()` / `from_entity()` hai chiều.
- [ ] T011 Tạo migration Alembic cập nhật cột `payload` cho bảng `permission_requests`.

### Phase 4: Use Cases & Dependency Injection Refactor
- [ ] T012 Tái cấu trúc `CreatePermissionRequestUseCase` ủy quyền toàn bộ cho `registry.get(category)` và Typed Payloads.
- [ ] T013 Tái cấu trúc `DeletePermissionRequestUseCase` ủy quyền dọn dẹp cho `strategy.on_deleted(...)`.
- [ ] T014 Đăng ký DI cho các Strategies và `PermissionStrategyRegistry` trong `backend/app/permission_request/providers.py`.
- [ ] T015 Đảm bảo schemas và controller giữ tính tương thích ngược cho Frontend (computed properties `start_time`, `meeting_id` trích xuất từ `payload`).

### Phase 5: Verification & Quality Control
- [ ] T016 Viết unit tests kiểm thử Generic Payloads và các Strategies trong `backend/tests/unit/test_permission_strategies.py`.
- [ ] T017 Chạy kiểm thử toàn bộ `pytest tests/unit/` đảm bảo 168/168 tests pass.
- [ ] T018 Chạy kiểm tra linter `ruff check app/permission_request/`.
