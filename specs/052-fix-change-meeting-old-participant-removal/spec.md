# Feature Specification: Tái cấu trúc phân tách Repository giữa Meeting và MeetingParticipant

**Feature Branch**: `052-fix-change-meeting-old-participant-removal`

**Created**: 2026-11-06

**Status**: Draft

**Input**: User description: "Tôi nghĩ tôi nên tách riêng ra meeting_repo chỉ CRUD liên quan đến bảng Meeting thôi, còn CRUD participant sẽ do meeting participant repo đảm nhận. Chú ý chỉ refactor thôi còn những yếu tố sau thì sẽ không thay đổi gì cả: Backend Auto-Discovery, Backend Validation old_meeting_id, Frontend Smart Selection."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phân tách Repository theo nguyên tắc Single Responsibility Principle (Priority: P1)

Hệ thống backend cần tách bạch rõ ràng trách nhiệm giữa việc lưu trữ buổi họp (`Meeting`) và lưu trữ người tham gia (`MeetingParticipant`). `MeetingRepository` chỉ đảm nhận CRUD bảng `meetings`. `ParticipantRepository` đảm nhận CRUD bảng `meeting_participants`. Khi học viên đổi lịch (`CHANGE_MEETING`), chiến lược `ChangeMeetingStrategy` gọi trực tiếp `participant_repo.remove_participant(old_meeting_id, user_id)` để xóa học viên khỏi buổi cũ và `participant_repo.add_participant(...)` để thêm vào buổi mới, không cần load toàn bộ Aggregate `Meeting` và không dùng diffing trong `MeetingRepository.save()`.

**Why this priority**: Loại bỏ khối logic diffing phức tạp, giải quyết triệt để lỗi không xóa người tham gia khỏi buổi cũ, tăng tốc độ xử lý và ngăn ngừa rủi ro xóa nhầm dữ liệu học viên.

**Independent Test**:
- Tạo 2 buổi họp A và B.
- Học viên U1 nằm trong Meeting A.
- Gọi luồng đổi lịch (`CHANGE_MEETING`) từ Meeting A sang Meeting B:
  - `participant_repo.remove_participant(A, U1)` được kích hoạt trực tiếp -> U1 biến mất khỏi bảng `meeting_participants` tại Meeting A.
  - `participant_repo.add_participant(B, U1)` được kích hoạt trực tiếp -> U1 xuất hiện tại Meeting B.
- Các bài kiểm thử unit test và integration test của Meeting và Permission Request chạy thành công.

**Acceptance Scenarios**:

1. **Given** Học viên U1 đang tham gia Meeting A và gửi đơn đổi lịch sang Meeting B (kèm `old_meeting_id = A`), **When** Hệ thống xử lý `on_created` trong `ChangeMeetingStrategy`, **Then** Học viên U1 bị xóa trực tiếp khỏi Meeting A thông qua `ParticipantRepository.remove_participant` và được thêm vào Meeting B.
2. **Given** Người dùng tạo buổi sinh hoạt mới kèm danh sách người tham gia ban đầu, **When** `CreateMeetingUseCase` thực thi, **Then** Buổi sinh hoạt được lưu qua `meeting_repo.save()`, sau đó danh sách người tham gia được tạo qua `participant_repo.bulk_create()`.
3. **Given** Người dùng cập nhật danh sách người tham gia của buổi sinh hoạt, **When** `UpdateMeetingUseCase` thực thi, **Then** Danh sách người tham gia được đồng bộ thông qua `participant_repo.sync_meeting_participants()`.

---

### Non-Goals (Phạm vi KHÔNG thay đổi theo yêu cầu người dùng)

- **KHÔNG làm Backend Auto-Discovery**: Không tự động dò tìm `old_meeting_id` nếu người dùng để trống.
- **KHÔNG thay đổi Backend Validation**: Không thêm ràng buộc kiểm tra xem người dùng có thực sự nằm trong `old_meeting_id` hay không ngoài các logic validate hiện có.
- **KHÔNG thay đổi Frontend Smart Selection**: Giữ nguyên giao diện và biểu mẫu chọn cuộc họp hiện tại.

---

### Edge Cases

- **Xóa participant khi không tồn tại**: `participant_repo.remove_participant` trả về `False` an toàn mà không làm sập giao dịch (fail-safe).
- **Thêm participant khi đã tồn tại trong buổi đích**: `participant_repo.add_participant` kiểm tra sự tồn tại (hoặc trạng thái `is_deleted`) để kích hoạt lại thay vì gây lỗi trùng lặp khóa chính / ràng buộc duy nhất.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `MeetingRepository.save()` MUST chỉ thực hiện lưu trữ các trường thuộc bảng `meetings` (`title`, `content`, `start_time`, `end_time`, `require_check_in`, `enable_evaluation`, `evaluation_deadline`, `created_by`). Khối mã diffing, đối soát `existing_user_ids` và `session.delete(old_p)` MUST bị loại bỏ hoàn toàn.
- **FR-002**: `ParticipantRepository` MUST bổ sung các phương thức chuyên biệt phục vụ thao tác người tham gia:
  - `remove_participant(meeting_id: int, user_id: int) -> bool`: Xóa người tham gia cụ thể khỏi buổi sinh hoạt.
  - `add_participant(domain: DomainParticipant) -> DomainParticipant`: Thêm mới hoặc kích hoạt lại người tham gia trong buổi sinh hoạt.
  - `bulk_create(meeting_id: int, participants: list[DomainParticipant]) -> list[DomainParticipant]`: Tạo hàng loạt người tham gia cho buổi sinh hoạt mới.
  - `sync_meeting_participants(meeting_id: int, new_trainers: set[int], new_trainees: set[int]) -> None`: Đồng bộ cập nhật danh sách Trainer và Trainee của buổi sinh hoạt.
- **FR-003**: `ChangeMeetingStrategy` MUST nhận `ParticipantRepository` (thông qua Dishka DI) và sử dụng:
  - `participant_repo.remove_participant(old_meeting_id, user_id)` khi có `old_meeting_id`.
  - `participant_repo.add_participant(...)` để thêm người tham gia vào buổi họp đích.
- **FR-004**: `CreateMeetingUseCase` MUST phối hợp sử dụng `meeting_repo.save()` để lưu thông tin buổi học và `participant_repo.bulk_create()` để lưu danh sách người tham gia ban đầu.
- **FR-005**: `UpdateMeetingUseCase` MUST phối hợp sử dụng `meeting_repo.save()` để cập nhật thông tin buổi học và `participant_repo.sync_meeting_participants()` để cập nhật danh sách người tham gia.
- **FR-006**: Dishka Provider ([`providers.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/permission_request/providers.py)) MUST inject `ParticipantRepository` vào `ChangeMeetingStrategy`.

### Key Entities

- **Buổi sinh hoạt (`Meeting`)**: Aggregate Root đại diện cho thông tin buổi họp.
- **Thành viên tham dự (`MeetingParticipant`)**: Thực thể đại diện cho sự hiện diện của một thành viên trong một buổi họp.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các đơn đổi lịch (`CHANGE_MEETING`) có `old_meeting_id` xóa thành công học viên khỏi buổi cũ ngay sau khi tạo đơn.
- **SC-002**: Tốc độ xử lý của hàm `MeetingRepository.save()` giảm ít nhất 50% thời gian thực thi do loại bỏ các câu truy vấn diffing và join không cần thiết.
- **SC-003**: Toàn bộ test suite unit test và API integration test hiện có của Meeting và Permission Request vượt qua 100% (Pass).
