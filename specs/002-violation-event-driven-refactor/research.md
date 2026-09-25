# Phase 0 Research: Event-Driven Violation Refactor

## 1. Architectural Decisions

### Decision 1: Phân tách ranh giới Bounded Context giữa các Domain
- **Quyết định**: Domain `Meeting` và `Homework` chỉ chịu trách nhiệm thu thập và phát hiện trạng thái thô của thành viên (vắng, trễ, chưa nộp bài) và phát tán Domain Event. Không domain nào ngoài `Violation` được phép quyết định hành vi đó có vi phạm hay không.
- **Lý do**:
  - Tuân thủ nguyên tắc **Single Responsibility (SRP)** và **Clean Architecture (Principle I của Constitution)**.
  - Loại bỏ hoàn toàn sự phụ thuộc chéo giữa `Meeting` / `Homework` với `Violation` và `PermissionRequest`.
  - Mọi quy tắc xử phạt, miễn trừ, tạo bản ghi vi phạm được gom về một nơi duy nhất.
- **Phương án thay thế đã cân nhắc**:
  - *Gọi trực tiếp qua RPC/Service giữa các domain*: Bị từ chối vì tạo ra khớp nối đồng bộ (tight coupling) và dễ gây lỗi vòng tròn (circular dependency).

### Decision 2: Cơ chế truyền tải sự kiện qua `EventBus`
- **Quyết định**: Sử dụng `app.shared.domain.event_bus.EventBus` hiện có để phát tán và đăng ký các sự kiện bất đồng bộ.
- **Lý do**:
  - Đã được định nghĩa sẵn trong hệ thống (`DomainEvent`, `EventHandler`).
  - Hỗ trợ publish async, không làm block luồng chính của Job hay API controller.

### Decision 3: Quản lý tính bất biến và chống trùng lặp (Idempotency)
- **Quyết định**: Trong `AutomatedViolationHandler`, trước khi tạo bản ghi `Violation`, kiểm tra xem vi phạm cho `(user_id, date, reason/event_ref)` đã tồn tại trong ngày hôm đó hay chưa.
- **Lý do**:
  - Đảm bảo khi job chạy lại hoặc rescan (`RescanAllHomeworksUseCase`), không bị sinh trùng hàng loạt biên bản vi phạm cho cùng một sự kiện.

---

## 2. Danh sách Domain Events cần chuẩn hóa

| Tên Event | Domain phát | Dữ liệu mang theo | Handler xử lý |
| :--- | :--- | :--- | :--- |
| `ParticipantAbsenceRecorded` | `Meeting` | `user_id`, `meeting_id`, `meeting_title`, `meeting_date` | `AutomatedViolationHandler` |
| `ParticipantLateRecorded` | `Meeting` | `user_id`, `meeting_id`, `meeting_title`, `check_in_at`, `start_time` | `AutomatedViolationHandler` |
| `HomeworkOverdueDetected` | `Homework` | `user_id`, `homework_id`, `homework_title`, `deadline_date`, `uncompleted_items` | `AutomatedViolationHandler` |

---

## 3. Tác động đến Dependency Injection (Dishka)

1. **`app/meeting/providers.py`**:
   - Xóa `create_violation_uc` và `permission_repo` khỏi định nghĩa `check_meeting_attendance_use_case`.
   - Giảm phụ thuộc từ 4 repo/service xuống 2 (`meeting_repo`, `participant_repo`).
2. **`app/homework/providers.py`**:
   - Xóa `permission_repo` khỏi `CheckOverdueHomeworkUseCase` (chuyển việc kiểm tra postpone về handler của violation).
3. **`app/violation/providers.py`**:
   - Đăng ký `AutomatedViolationHandler` với các dependencies: `create_violation_use_case`, `permission_repo`, `participant_repo`, `violation_repo`.
4. **`app/core/events.py`**:
   - Đăng ký `AutomatedViolationHandler` lắng nghe `ParticipantAbsenceRecorded`, `ParticipantLateRecorded`, `HomeworkOverdueDetected`.
