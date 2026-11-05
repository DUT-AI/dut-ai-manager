# Tasks: Tái Cấu Trúc Phân Tách Repository Giữa Meeting Và MeetingParticipant

**Input**: Design documents from `specs/052-fix-change-meeting-old-participant-removal/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/change-meeting-contract.md`, `quickstart.md`  
**Tests**: Bao gồm kiểm thử tự động với `pytest` cho unit test use case, strategy và integration test API.  
**Organization**: Nhiệm vụ được chia thành các phase tuần tự và phân tách theo User Story 1 (P1).

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Có thể thực hiện song song (các file độc lập, không phụ thuộc task trước đó)
- **[US1]**: Thuộc User Story 1 (P1)

---

## Phase 1: Setup & Baseline Verification

**Purpose**: Xác minh trạng thái baseline của các bộ test trước khi can thiệp mã nguồn

- [x] T001 Chạy kiểm thử baseline hiện tại của meeting và change meeting trong `backend/tests/unit/test_change_meeting_permission_request.py` và `backend/tests/api/test_change_meeting_api.py`

---

## Phase 2: Foundational (Mở rộng `ParticipantRepository`)

**Purpose**: Trang bị đầy đủ các phương thức thao tác CRUD chuyên biệt trên bảng `meeting_participants` trước khi tách khỏi `MeetingRepository`

- [x] T002 Bổ sung phương thức `remove_participant(meeting_id: int, user_id: int) -> bool` trong `backend/app/meeting/infrastructure/repositories/participant_repository.py` để xóa trực tiếp dòng participant khỏi database
- [x] T003 [P] Bổ sung phương thức `add_participant(domain: DomainParticipant) -> DomainParticipant` trong `backend/app/meeting/infrastructure/repositories/participant_repository.py` để thêm mới hoặc kích hoạt lại participant trong buổi họp
- [x] T004 [P] Bổ sung phương thức `bulk_create(meeting_id: int, participants: list[DomainParticipant]) -> list[DomainParticipant]` trong `backend/app/meeting/infrastructure/repositories/participant_repository.py` để lưu danh sách người tham gia ban đầu
- [x] T005 Bổ sung phương thức `sync_meeting_participants(meeting_id: int, new_trainers: set[int], new_trainees: set[int]) -> None` trong `backend/app/meeting/infrastructure/repositories/participant_repository.py` để đồng bộ danh sách Trainer và Trainee

**Checkpoint**: `ParticipantRepository` đã có đầy đủ các phương thức CRUD độc lập cho `meeting_participants`.

---

## Phase 3: User Story 1 - Phân tách Repository & Cập nhật Use Cases (Priority: P1) 🎯 MVP

**Goal**: Phân tách rạch ròi trách nhiệm giữa `MeetingRepository` và `ParticipantRepository`, cập nhật các use case gọi trực tiếp `ParticipantRepository`, chấm dứt việc diffing/hard-delete bên trong `MeetingRepository.save()`.

**Independent Test**:
- Gọi đổi lịch từ Meeting A sang Meeting B: Học viên bị rút khỏi Meeting A qua `participant_repo.remove_participant` và được ghi danh vào Meeting B qua `participant_repo.add_participant`.
- `CreateMeetingUseCase` và `UpdateMeetingUseCase` phối hợp nhịp nhàng giữa `meeting_repo` và `participant_repo`.

### Implementation for User Story 1

- [x] T006 [US1] Tinh gọn hàm `save()` trong `backend/app/meeting/infrastructure/repositories/meeting_repository.py`: loại bỏ hoàn toàn khối mã diffing `existing_user_ids`, đối soát và `session.delete(old_p)`, chỉ lưu các thuộc tính thuộc bảng `meetings`
- [x] T007 [US1] Cập nhật Dishka Provider trong `backend/app/permission_request/providers.py` để inject `ParticipantRepository` vào `ChangeMeetingStrategy`
- [x] T008 [US1] Tái cấu trúc `ChangeMeetingStrategy` trong `backend/app/permission_request/application/strategies/change_meeting_strategy.py`: nhận `participant_repo`, gọi trực tiếp `participant_repo.remove_participant` khi có `old_meeting_id` và `participant_repo.add_participant` cho buổi mới
- [x] T009 [US1] Cập nhật `CreateMeetingUseCase` trong `backend/app/meeting/application/create_meeting_use_case.py`: inject `ParticipantRepository`, lưu meeting qua `meeting_repo.save()`, sau đó gọi `participant_repo.bulk_create()`
- [x] T010 [US1] Cập nhật `UpdateMeetingUseCase` trong `backend/app/meeting/application/update_meeting_use_case.py`: inject `ParticipantRepository`, lưu thông tin meeting qua `meeting_repo.save()`, sau đó gọi `participant_repo.sync_meeting_participants()`
- [x] T011 [US1] Cập nhật Dishka Provider trong `backend/app/meeting/providers.py` để inject `ParticipantRepository` vào `CreateMeetingUseCase` và `UpdateMeetingUseCase`
- [x] T012 [P] [US1] Cập nhật mock và assertion trong unit test `backend/tests/unit/test_change_meeting_permission_request.py` phù hợp với chữ ký `ParticipantRepository` mới
- [x] T013 [P] [US1] Cập nhật mock và assertion trong unit test `backend/tests/unit/test_meeting_use_cases.py` cho `CreateMeetingUseCase` và `UpdateMeetingUseCase`

**Checkpoint**: Hoàn tất phân tách 2 Repository và cập nhật toàn bộ các use cases liên quan.

---

## Phase 4: Polish & Integration Verification

**Purpose**: Xác minh toàn diện độ ổn định, không gây hồi quy (Zero Regression)

- [x] T014 Chạy integration test API đổi ca trong `backend/tests/api/test_change_meeting_api.py` để xác nhận DB state sau khi chuyển ca
- [x] T015 Chạy toàn bộ test suite liên quan đến meeting và permission trong `backend/tests/unit/` và `backend/tests/api/`
- [x] T016 Chạy linter `ruff check backend/app` để đảm bảo chuẩn hóa cú pháp, kiểu dữ liệu và import sạch sẽ

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Không phụ thuộc, chạy baseline test.
- **Phase 2 (Foundational)**: Xây dựng các hàm mới trên `ParticipantRepository` (T002 - T005).
- **Phase 3 (User Story 1)**: Phụ thuộc vào Phase 2 hoàn thành. Tinh gọn `MeetingRepository.save()`, cập nhật use cases, DI providers và unit tests.
- **Phase 4 (Polish & Verification)**: Chạy full integration test và linting.

### Parallel Opportunities
- T003 và T004 có thể triển khai song song trong Phase 2.
- T012 và T013 có thể cập nhật song song cho các file test riêng biệt.

---

## Implementation Strategy (MVP First)

1. **Bước 1**: Viết bổ sung các phương thức chuyên trách trên `ParticipantRepository` (T002 - T005).
2. **Bước 2**: Tinh gọn `MeetingRepository.save()` và cập nhật `ChangeMeetingStrategy` (T006 - T008) -> **Khắc phục ngay lập tức lỗi không xóa participant cũ**.
3. **Bước 3**: Cập nhật `CreateMeetingUseCase` và `UpdateMeetingUseCase` (T009 - T011).
4. **Bước 4**: Cập nhật test cases và chạy full verification (T012 - T016).
