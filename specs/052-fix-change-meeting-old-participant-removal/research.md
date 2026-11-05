# Phase 0: Research & Architectural Decisions

## Feature: Tái cấu trúc phân tách Repository giữa Meeting và MeetingParticipant

---

### Scope Clarification & User Constraints

Theo yêu cầu cụ thể của người dùng, phạm vi triển khai **chỉ tập trung hoàn toàn vào Refactoring phân tách Repository**, không thay đổi các logic nghiệp vụ sau:
1. ❌ **Không làm Backend Auto-Discovery**: Giữ nguyên cơ chế hiện tại, nếu người dùng để trống `old_meeting_id` thì xem như đăng ký mới.
2. ❌ **Không thay đổi Backend Validation**: Không thêm validation bắt buộc học viên phải có mặt trong `old_meeting_id`.
3. ❌ **Không thay đổi Frontend Smart Selection**: Giữ nguyên biểu mẫu và logic dropdown chọn meeting hiện tại ở Frontend.

---

### Architectural Decisions

#### Decision 1: Phân tách trách nhiệm (SRP) giữa `MeetingRepository` và `ParticipantRepository`

- **Quyết định (Decision)**:
  - Loại bỏ hoàn toàn khối logic diffing, cập nhật và hard-delete `meeting_participants` bên trong hàm `MeetingRepository.save()`. `MeetingRepository` chỉ đảm nhận CRUD dữ liệu trên bảng `meetings`.
  - Toàn bộ các thao tác liên quan đến `meeting_participants` được chuyển giao và chuẩn hóa trên `ParticipantRepository`:
    - `remove_participant(meeting_id: int, user_id: int) -> bool`: Xóa người tham gia khỏi buổi họp cũ.
    - `add_participant(domain: DomainParticipant) -> DomainParticipant`: Thêm mới/kích hoạt lại người tham gia vào buổi họp.
    - `bulk_create(meeting_id: int, participants: list[DomainParticipant]) -> list[DomainParticipant]`: Tạo danh sách thành viên ban đầu khi tạo meeting mới (dùng cho `CreateMeetingUseCase`).
    - `sync_meeting_participants(meeting_id: int, new_trainers: set[int], new_trainees: set[int])`: Đồng bộ danh sách Trainer và Trainee (dùng cho `UpdateMeetingUseCase`).
- **Lý do (Rationale)**:
  - **Tuân thủ Clean Architecture & Hiến pháp I (Clean Architecture & Practical DDD Boundaries)**: Mỗi Repository chỉ chịu trách nhiệm cho một bảng/aggregate boundary tương ứng.
  - **Triệt tiêu nguy cơ xóa nhầm dữ liệu (Accidental Data Loss)**: Trước đây, nếu `domain.participants` bị truyền thiếu do phân trang hoặc query thiếu, `save()` sẽ tự động xóa sạch các participants khác trong database.
  - **Tối ưu hiệu năng**: Không còn phải load toàn bộ Aggregate Meeting kèm 30–50 participants cùng quan hệ User/Creator vào bộ nhớ chỉ để rút 1 học viên.

#### Decision 2: Triển khai trực tiếp trên `ChangeMeetingStrategy`

- **Quyết định (Decision)**:
  - Inject `ParticipantRepository` vào `ChangeMeetingStrategy` thông qua Dishka Provider (`providers.py`).
  - Trong `on_created`:
    ```python
    if old_meeting_id:
        self.participant_repo.remove_participant(old_meeting_id, user_id)
        self.permission_repo.cancel_active_requests_by_meeting(user_id=user_id, meeting_id=old_meeting_id)

    self.participant_repo.add_participant(
        MeetingParticipant(
            meeting_id=meeting_id,
            user_id=user_id,
            status=ParticipantStatus.NOT_JOINED,
            role=ParticipantRole.TRAINEE,
        )
    )
    ```
- **Lý do (Rationale)**:
  - Rút ngắn chu trình từ ~4 truy vấn phức tạp (load meeting, load relations, select participants, diffing loop, session delete, refresh) xuống chỉ còn 1 câu lệnh `DELETE` và 1 câu lệnh `INSERT/UPDATE` trực tiếp.

#### Decision 3: Đồng bộ hóa `CreateMeetingUseCase` và `UpdateMeetingUseCase`

- **Quyết định (Decision)**:
  - `CreateMeetingUseCase`: Gọi `meeting_repo.save(meeting)` để lấy `saved_meeting.id`, sau đó gọi `participant_repo.bulk_create(saved_meeting.id, participants)`.
  - `UpdateMeetingUseCase`: Gọi `meeting_repo.save(meeting)` để cập nhật các thuộc tính của meeting, sau đó gọi `participant_repo.sync_meeting_participants(meeting.id, new_trainers_set, new_trainees_set)`.
- **Lý do (Rationale)**:
  - Phân tách rõ ràng giữa việc cập nhật buổi học và cập nhật thành viên lớp.
