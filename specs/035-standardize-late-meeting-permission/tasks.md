# Tasks: Standardize Late Meeting Permission

**Input**: Design documents from `/specs/035-standardize-late-meeting-permission/`
**Prerequisites**: plan.md, spec.md, research.md

## Execution Checklist

### Phase 1: Domain Entities & Invariants
- [X] T001 Bổ sung phương thức `validate_late(meeting: Meeting, now: datetime | None = None)` trong `backend/app/permission_request/domain/entity.py`
- [X] T002 Cập nhật `MeetingParticipant.check_in` trong `backend/app/meeting/domain/entity.py` để xử lý chuẩn xác trạng thái đến đúng giờ (`JOINED`) dù có đơn xin trễ

### Phase 2: Repository Operations
- [X] T003 Thêm phương thức `mark_participant_late_excused(meeting_id: int, user_id: int)` và cập nhật `revert_participant_excused(meeting_id: int, user_id: int)` trong `backend/app/permission_request/infrastructure/repository.py`

### Phase 3: Use Cases & Providers Refactor
- [X] T004 Tích hợp `MeetingRepository` và gọi `request.validate_late` cùng `mark_participant_late_excused` trong `backend/app/permission_request/application/create_permission_request_use_case.py`
- [X] T005 Cập nhật `backend/app/permission_request/providers.py` để truyền `MeetingRepository` vào `CreatePermissionRequestUseCase`
- [X] T006 Cập nhật `backend/app/permission_request/application/delete_permission_request_use_case.py` để revert `LATE_EXCUSED` về `NOT_JOINED` khi xóa đơn

### Phase 4: Unit Testing & Verification
- [X] T007 Thêm unit tests cho domain validation và use cases của đơn xin đi trễ trong `backend/tests/unit/test_late_meeting_permission.py`
- [X] T008 Chạy toàn bộ test suite `pytest tests/unit/` đảm bảo zero regression (168/168 passed)
