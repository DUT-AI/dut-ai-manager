# Tasks: Modular Permission Request Use Cases

**Input**: Design documents from `/specs/034-modular-permission-request/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

## Execution Checklist

### Phase 1: Create Individual Use Case Files
- [X] T001 [P] Tạo `backend/app/permission_request/application/get_permission_requests_use_case.py`
- [X] T002 [P] Tạo `backend/app/permission_request/application/create_permission_request_use_case.py`
- [X] T003 [P] Tạo `backend/app/permission_request/application/update_permission_request_use_case.py`
- [X] T004 [P] Tạo `backend/app/permission_request/application/delete_permission_request_use_case.py`
- [X] T005 [P] Tạo `backend/app/permission_request/application/restore_permission_request_use_case.py`

### Phase 2: Update Package Init & Consumers
- [X] T006 Cập nhật `backend/app/permission_request/application/__init__.py` import từng use case từ file riêng và export trong `__all__`
- [X] T007 Cập nhật imports trong `backend/app/permission_request/controller.py`
- [X] T008 Cập nhật imports trong `backend/app/permission_request/providers.py`
- [X] T009 Xóa file cũ `backend/app/permission_request/application/use_cases.py`

### Phase 3: Validation & Quality Gate
- [X] T010 Chạy `uv run --directory backend ruff check app/permission_request/`
- [X] T011 Chạy `uv run --directory backend pytest tests/unit/`
