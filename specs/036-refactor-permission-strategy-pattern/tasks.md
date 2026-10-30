# Tasks: Generic Payload Entity & Strategy Pattern

**Input**: Design documents from `/specs/036-refactor-permission-strategy-pattern/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

## Execution Checklist

### Phase 1: Domain Value Objects & Generic Entity
- [x] T001 [P] Tạo các Typed Payloads trong `backend/app/permission_request/domain/payloads.py`
- [x] T002 Cập nhật `backend/app/permission_request/domain/entity.py` thành Generic Entity `PermissionRequest[TPayload]`

### Phase 2: Strategy Pattern Implementation
- [x] T003 [P] Tạo `PermissionStrategy[TPayload]` trong `backend/app/permission_request/application/strategies/base.py`
- [x] T004 [P] Tạo `AbsenceStrategy` trong `backend/app/permission_request/application/strategies/absence_strategy.py`
- [x] T005 [P] Tạo `LateStrategy` trong `backend/app/permission_request/application/strategies/late_strategy.py`
- [x] T006 [P] Tạo `PostponeStrategy` trong `backend/app/permission_request/application/strategies/postpone_strategy.py`
- [x] T007 [P] Tạo `OtherStrategy` trong `backend/app/permission_request/application/strategies/other_strategy.py`
- [x] T008 Tạo `PermissionStrategyRegistry` trong `backend/app/permission_request/application/strategies/registry.py`
- [x] T009 Export sạch sẽ trong `backend/app/permission_request/application/strategies/__init__.py`

### Phase 3: Storage & Model Refactor (JSONB Payload)
- [x] T010 Cập nhật ORM Model `backend/app/permission_request/infrastructure/model.py` bổ sung cột `payload JSON` / `JSONB` và ánh xạ `to_entity()` / `from_entity()`
- [x] T011 Tạo migration Alembic cập nhật cột `payload` cho bảng `permission_requests`

### Phase 4: Use Cases & Dependency Injection Refactor
- [x] T012 Tái cấu trúc `CreatePermissionRequestUseCase` ủy quyền toàn bộ cho `registry.get(category)` và Typed Payloads
- [x] T013 Tái cấu trúc `DeletePermissionRequestUseCase` ủy quyền dọn dẹp cho `strategy.on_deleted(...)`
- [x] T014 Đăng ký DI cho các Strategies và `PermissionStrategyRegistry` trong `backend/app/permission_request/providers.py`
- [x] T015 Đảm bảo schemas và controller giữ tính tương thích ngược cho Frontend

### Phase 5: Verification & Quality Control
- [x] T016 Viết unit tests kiểm thử Generic Payloads và các Strategies trong `backend/tests/unit/test_permission_strategies.py`
- [x] T017 Chạy kiểm thử toàn bộ `pytest tests/unit/` đảm bảo 100% tests pass
- [x] T018 Chạy kiểm tra linter `ruff check app/permission_request/`

