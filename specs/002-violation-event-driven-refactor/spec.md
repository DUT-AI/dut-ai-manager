# Feature Specification: Refactor Kiến Trúc Violation Domain Theo Mô Hình Event-Driven

**Feature Branch**: `002-violation-event-driven-refactor`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "Refactor kiến trúc Violation Domain theo mô hình Event-Driven: Tách rời hoàn toàn logic xử lý vi phạm khỏi domain Meeting và Homework. Các domain chỉ phát Domain Event, domain Violation sẽ lắng nghe và tự quyết định xử lý vi phạm"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tự động phát hiện và xử lý vi phạm điểm danh từ sự kiện Meeting (Priority: P1)

Khi một buổi sinh hoạt/họp kết thúc hoặc khi tác vụ quét điểm danh định kỳ chạy, domain Meeting chỉ đánh giá trạng thái tham dự của từng thành viên và phát ra các Domain Event tương ứng (như `ParticipantAbsenceRecorded`, `ParticipantLateRecorded`). Domain Violation lắng nghe các sự kiện này qua EventBus, tự đối soát với chính sách miễn trừ (đơn xin phép) và tự quyết định tạo biên bản vi phạm nếu không hợp lệ.

**Why this priority**: Đảm bảo nghiệp vụ kỷ luật điểm danh hoạt động ổn định và chính xác mà không làm domain Meeting bị gắn chặt với logic xử lý vi phạm.

**Independent Test**: Kích hoạt việc phát một sự kiện `ParticipantAbsenceRecorded(user_id=1, meeting_id=10)` trên EventBus. Kiểm tra xem Handler của Violation Domain có tự động bắt sự kiện, tra cứu đơn xin phép và tạo bản ghi vi phạm tương ứng hay không.

**Acceptance Scenarios**:

1. **Given** sự kiện `ParticipantAbsenceRecorded` được phát cho thành viên không có đơn xin vắng, **When** Violation Event Handler tiếp nhận sự kiện, **Then** hệ thống tự động tạo 01 biên bản vi phạm vắng sinh hoạt không phép cho thành viên.
2. **Given** sự kiện `ParticipantAbsenceRecorded` được phát cho thành viên đã có đơn xin vắng được duyệt, **When** Violation Event Handler xử lý, **Then** hệ thống ghi nhận miễn trừ vi phạm và KHÔNG tạo bản ghi vi phạm.
3. **Given** sự kiện `ParticipantLateRecorded` được phát cho thành viên check-in trễ và không có đơn xin trễ hợp lệ, **When** Violation Event Handler xử lý, **Then** hệ thống tự động tạo 01 biên bản vi phạm đi trễ không phép.

---

### User Story 2 - Tự động phát hiện và xử lý vi phạm nộp bài từ sự kiện Homework (Priority: P1)

Khi đến hạn nộp bài tập hoặc tác vụ kiểm tra bài tập chạy, domain Homework chỉ chịu trách nhiệm xác định danh sách các thành viên chưa nộp bài hoặc nộp trễ và phát Domain Event (như `HomeworkOverdueDetected`). Domain Violation sẽ tiếp nhận sự kiện và chịu trách nhiệm tạo biên bản vi phạm theo quy tắc xử lý bài tập.

**Why this priority**: Đồng bộ hóa kiến trúc Event-Driven trên toàn bộ hệ thống cho cả bài tập và điểm danh.

**Independent Test**: Phát một sự kiện `HomeworkOverdueDetected(user_id=2, homework_id=5, homework_title="Lab 1")` lên EventBus và xác nhận 01 biên bản vi phạm quá hạn bài tập được tạo trong domain Violation.

**Acceptance Scenarios**:

1. **Given** sự kiện `HomeworkOverdueDetected` được phát ra từ domain Homework, **When** Violation Event Handler tiếp nhận, **Then** hệ thống tạo 01 biên bản vi phạm quá hạn bài tập gắn đúng mã người dùng, tiêu đề bài tập và thời điểm vi phạm.

---

### User Story 3 - Tách rời hoàn toàn sự phụ thuộc (Zero Coupling) giữa các Domain (Priority: P2)

Mã nguồn của domain `Meeting` và `Homework` hoàn toàn sạch sẽ, không import hay gọi trực tiếp bất kỳ Use Case, Service hay Repository nào thuộc domain `Violation` hoặc `PermissionRequest`.

**Why this priority**: Tuân thủ nguyên tắc Clean Architecture & Single Responsibility, giúp từng domain có thể mở rộng, bảo trì hoặc kiểm thử độc lập mà không gây lỗi dây chuyền.

**Independent Test**: Quét phân tích tĩnh mã nguồn trong thư mục `backend/app/meeting` và `backend/app/homework` để xác nhận không còn bất kỳ import nào trỏ đến `app.violation` hay `CreateViolationUseCase`.

**Acceptance Scenarios**:

1. **Given** `CheckMeetingAttendanceUseCase` trong domain Meeting, **When** thực thi kiểm tra điểm danh, **Then** use case chỉ tương tác với `MeetingRepository`, `ParticipantRepository` và `EventBus`, không chứa logic xử phạt hay tạo vi phạm.
2. **Given** tác vụ kiểm tra bài tập trong domain Homework, **When** thực thi, **Then** use case chỉ tương tác với dữ liệu bài tập và phát sự kiện qua `EventBus`.

---

### User Story 4 - Tập trung hoá quy tắc xét duyệt miễn trừ vi phạm tại Domain Violation (Priority: P2)

Tất cả các logic nghiệp vụ liên quan đến việc: kiểm tra đơn xin phép (`PermissionRequest`), đánh giá tính hợp lệ của đơn theo khung thời gian, cấu hình lý do phạt và loại vi phạm (System Violation) được tập trung duy nhất tại domain `Violation`.

**Why this priority**: Khi có sự thay đổi về chính sách kỷ luật (ví dụ: thay đổi thời gian ân hạn, thêm quy tắc miễn trừ mới), nhà phát triển chỉ cần chỉnh sửa tại một nơi duy nhất (Domain Violation).

**Independent Test**: Thay đổi quy tắc kiểm tra đơn trong Violation Handler và kiểm thử xác nhận hành vi thay đổi mà không cần chạm vào domain Meeting hay Homework.

**Acceptance Scenarios**:

1. **Given** quy tắc đánh giá đơn xin phép được nâng cấp trong domain Violation, **When** có sự kiện điểm danh trễ từ Meeting gửi sang, **Then** Violation Domain áp dụng quy tắc mới một cách độc lập và chính xác.

---

### Edge Cases

- **Mất kết nối hoặc lỗi trong Event Handler**: Khi handler của Violation gặp lỗi xử lý, lỗi này không được làm gián đoạn hoặc rollback luồng hoàn thành của buổi họp hay bài tập trong domain phát sự kiện.
- **Trùng lặp sự kiện (Duplicate Events)**: Nếu một sự kiện vắng/trễ bị phát nhiều lần cho cùng một người dùng và cùng một buổi họp/bài tập trong ngày, Violation Domain phải có cơ chế kiểm tra chống tạo trùng biên bản vi phạm (Idempotent Violation Creation).
- **Sự kiện mang dữ liệu không hợp lệ (Invalid User ID hoặc Meeting ID)**: Handler phải bắt lỗi, ghi log cảnh báo chi tiết và bỏ qua mà không làm crash ứng dụng.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI định nghĩa các Domain Event chuẩn cho việc ghi nhận sự kiện vắng mặt (`ParticipantAbsenceRecorded`) và đi trễ (`ParticipantLateRecorded`) trong domain Meeting.
- **FR-002**: Hệ thống PHẢI định nghĩa Domain Event chuẩn cho việc quá hạn bài tập (`HomeworkOverdueRecorded` / `HomeworkOverdueDetected`) trong domain Homework.
- **FR-003**: Domain `Meeting` PHẢI loại bỏ hoàn toàn mọi tham chiếu trực tiếp đến `CreateViolationUseCase` và `PermissionRequestRepository`.
- **FR-004**: Domain `Homework` PHẢI loại bỏ hoàn toàn mọi tham chiếu trực tiếp đến `CreateViolationUseCase`.
- **FR-005**: Domain `Violation` PHẢI cung cấp `AutomatedViolationHandler` đăng ký với `EventBus` để lắng nghe tất cả các sự kiện có khả năng cấu thành vi phạm từ các domain khác.
- **FR-006**: `AutomatedViolationHandler` PHẢI tự đảm nhiệm việc tra cứu đơn xin phép (`PermissionRequestRepository`) khi xử lý sự kiện vắng hoặc trễ từ Meeting.
- **FR-007**: `AutomatedViolationHandler` PHẢI tự động khởi tạo biên bản vi phạm hệ thống (`is_system=True`) khi xác định hành vi không có đơn xin phép hợp lệ.
- **FR-008**: Hệ thống PHẢI đảm bảo cơ chế chống tạo trùng biên bản vi phạm (kiểm tra xem vi phạm cho cùng user, cùng ngày và cùng sự kiện đã tồn tại chưa trước khi tạo).
- **FR-009**: Hệ thống PHẢI đảm bảo toàn bộ thời gian ghi nhận vi phạm tuân thủ múi giờ chuẩn **UTC+7 (Asia/Ho_Chi_Minh)**.
- **FR-010**: Hệ thống PHẢI đảm bảo các bài kiểm thử tự động (Unit Tests) cho Meeting và Violation được cập nhật và vượt qua 100% sau khi refactor.

---

### Key Entities *(include if feature involves data)*

- **Sự kiện Vắng mặt (`ParticipantAbsenceRecorded`)**: Domain Event chứa thông tin: `user_id`, `meeting_id`, `meeting_title`, `meeting_date`, `recorded_at`.
- **Sự kiện Đi trễ (`ParticipantLateRecorded`)**: Domain Event chứa thông tin: `user_id`, `meeting_id`, `meeting_title`, `check_in_at`, `start_time`, `recorded_at`.
- **Sự kiện Quá hạn bài tập (`HomeworkOverdueRecorded`)**: Domain Event chứa thông tin: `user_id`, `homework_id`, `homework_title`, `due_date`, `recorded_at`.
- **Biên bản Vi phạm (`Violation`)**: Thực thể lưu trữ vi phạm gồm `user_id`, `reason`, `date`, `is_system`, `created_at`.
- **Đơn xin phép (`PermissionRequest`)**: Thực thể dùng để đối soát miễn trừ vi phạm (loại đơn: `ABSENCE`, `LATE`).

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Độ phụ thuộc trực tiếp (Coupling Score) giữa domain `Meeting`/`Homework` với domain `Violation` giảm về **0 import**.
- **SC-002**: 100% các trường hợp vắng không phép, trễ không phép và quá hạn bài tập vẫn được ghi nhận vi phạm chính xác thông qua luồng EventBus.
- **SC-003**: 100% các trường hợp có đơn xin phép hợp lệ được miễn trừ vi phạm chính xác mà không cần domain Meeting phải xử lý.
- **SC-004**: Toàn bộ hệ thống test suite hiện tại và các test suite mới cho Event-Driven Violation đạt tỷ lệ Pass **100%** (Zero Regression).

---

## Assumptions

- `EventBus` trong `app.shared.domain.event_bus` hỗ trợ đăng ký (subscribe) và phát tán (publish) các sự kiện bất đồng bộ một cách tin cậy.
- Domain `Violation` được phép inject `PermissionRequestRepository` để phục vụ việc xét duyệt miễn trừ vi phạm.
- Các API endpoints trả về kết quả cho phía Client của cả Meeting, Homework và Violation giữ nguyên định dạng, không gây ảnh hưởng đến Frontend Web và Zalo Mini App.
