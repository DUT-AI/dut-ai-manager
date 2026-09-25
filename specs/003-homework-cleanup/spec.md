# Feature Specification: Tối Ưu Và Dọn Dẹp Domain Homework

**Feature Branch**: `003-homework-cleanup`

**Created**: 2026-09-25

**Status**: Draft

**Input**: User description: "Tối ưu và dọn dẹp domain Homework: Xóa bảng homework_teams, xóa HomeworkTeamModel, chuyển phân công team sang UI tự phân giải user_ids lưu vào homework_assignees, và xóa bỏ hoàn toàn các class/DTO legacy HomeworkSubmission"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Phân công bài tập hoàn toàn qua danh sách cá nhân (Priority: P1)

Quản trị viên / Leader khi tạo hoặc chỉnh sửa bài tập có thể phân công cho các thành viên. Giao diện (UI) chịu trách nhiệm cho phép chọn cá nhân hoặc chọn nhóm (team) và tự động phân giải thành danh sách `user_ids` duy nhất trước khi gửi về Backend. Backend chỉ nhận mảng `assignee_ids` và lưu trữ trực tiếp vào bảng `homework_assignees`.

**Why this priority**: Đơn giản hóa kiến trúc dữ liệu của bài tập, loại bỏ sự phức tạp của việc mapping qua bảng phụ `homework_teams`, giảm thiểu rủi ro lệch dữ liệu phân công.

**Independent Test**: Gọi API tạo bài tập mới kèm `assignee_ids=[1, 2, 3]`. Kiểm tra trong DB các bản ghi được lưu vào `homework_assignees` và API lấy chi tiết trả về đúng `assignee_ids`.

**Acceptance Scenarios**:

1. **Given** thông tin tạo bài tập hợp lệ với danh sách `assignee_ids`, **When** gửi yêu cầu tạo bài tập, **Then** hệ thống lưu bài tập và danh sách người phân công vào `homework_assignees`, trả về thông tin bài tập thành công.
2. **Given** bài tập đã tồn tại, **When** cập nhật bài tập với danh sách `assignee_ids` mới, **Then** hệ thống đồng bộ lại bảng `homework_assignees` khớp chính xác với danh sách mới.
3. **Given** bài tập đã được phân công, **When** lấy chi tiết bài tập, **Then** phản hồi trả về danh sách `assignee_ids` đầy đủ.

---

### User Story 2 - Loại bỏ bảng dữ liệu cũ và thực thể legacy HomeworkSubmission (Priority: P1)

Toàn bộ nghiệp vụ kiểm tra trạng thái nộp bài tập hiện tại đều được đối soát theo thời gian thực với Quiz API (Coding và Game). Do đó, các bảng và model lưu submission nội bộ cũ (`HomeworkSubmission`, `HomeworkTeamModel`, các DTO submit bài cũ) được loại bỏ hoàn toàn khỏi mã nguồn và database.

**Why this priority**: Giảm nợ kỹ thuật (technical debt), dọn sạch code thừa, tránh nhầm lẫn cho lập trình viên và tăng tốc độ bảo trì hệ thống.

**Independent Test**: Kiểm tra mã nguồn không còn `HomeworkTeamModel`, `HomeworkSubmission`, và kiểm tra migration Alembic drop bảng `homework_teams` thành công.

**Acceptance Scenarios**:

1. **Given** cơ sở dữ liệu hiện tại có bảng `homework_teams`, **When** chạy migration Alembic mới, **Then** bảng `homework_teams` được xóa bỏ hoàn toàn.
2. **Given** yêu cầu kiểm tra trạng thái nộp bài `GET /homeworks/{id}/submission-status`, **When** gọi API, **Then** hệ thống tiếp tục trả về thông tin nộp bài chính xác thông qua Quiz API mà không phụ thuộc vào bảng submission cũ.

---

### User Story 3 - Kiểm tra bài tập quá hạn độc lập không phụ thuộc TeamRepository (Priority: P2)

Tác vụ chạy ngầm định kỳ kiểm tra bài tập quá hạn (`CheckOverdueHomeworkUseCase`) xác định danh sách người cần nộp bài trực tiếp từ `assignee_ids` của bài tập mà không cần truy vấn phân giải nhóm qua `TeamRepository`.

**Why this priority**: Giảm phụ thuộc giữa domain Homework và Team, tăng tốc độ xử lý của tác vụ background quét bài tập quá hạn.

**Independent Test**: Chạy `CheckOverdueHomeworkUseCase` cho bài tập có hạn nộp trong ngày và xác nhận sự kiện `HomeworkOverdueDetected` được phát ra đúng cho các thành viên chưa hoàn thành trong `assignee_ids`.

**Acceptance Scenarios**:

1. **Given** bài tập có deadline đến hạn với danh sách `assignee_ids`, **When** `CheckOverdueHomeworkUseCase` thực thi, **Then** hệ thống đối soát từng user trong `assignee_ids` với Quiz API và phát sự kiện quá hạn cho những ai chưa hoàn thành.

---

### User Story 4 - Chuẩn hóa Single Responsibility cho các Use Case trong Homework (Priority: P2)

Mỗi Use Case trong domain `Homework` được tổ chức thành 1 file Python riêng biệt trong thư mục `app/homework/application/` (ví dụ `create_homework_use_case.py`, `get_homeworks_use_case.py`, `update_homework_use_case.py`, `delete_homework_use_case.py`, `check_overdue_homework_use_case.py`, `rescan_all_homeworks_use_case.py`, `get_homework_submission_status_use_case.py`) và export tập trung qua `__init__.py`.

**Why this priority**: Tuân thủ chuẩn kiến trúc Clean Architecture nhất quán trên toàn bộ dự án (tương tự Violation và Meeting domain).

**Independent Test**: Kiểm tra cấu trúc thư mục `app/homework/application` để đảm bảo mỗi use case là 1 file riêng và không còn file gom lớn (`crud_use_cases.py`, `checker_use_cases.py`, `submission_use_cases.py`).

**Acceptance Scenarios**:

1. **Given** thư mục `app/homework/application`, **When** kiểm tra danh sách file, **Then** mỗi Use Case nằm trong 1 file `*_use_case.py` riêng biệt và export qua `__init__.py`.

---

### Edge Cases

- **Danh sách `assignee_ids` có phần tử trùng lặp**: Backend tự động loại bỏ trùng lặp (dedup) trước khi lưu vào DB.
- **Danh sách `assignee_ids` rỗng**: Cho phép tạo bài tập không có người được phân công nếu cần lưu nháp, hoặc trả về lỗi validation nếu bài tập bắt buộc có người nhận.
- **Bài tập cũ đã tạo trước đây**: Dữ liệu trong `homework_assignees` được giữ nguyên vẹn, bài tập chỉ chứa `assignee_ids`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI lưu trữ toàn bộ danh sách thành viên được phân công bài tập duy nhất qua bảng `homework_assignees` (`HomeworkAssigneeModel`) với danh sách `assignee_ids`.
- **FR-002**: Hệ thống PHẢI loại bỏ hoàn toàn `HomeworkTeamModel`, quan hệ `teams` trong `HomeworkModel`, và trường `team_ids` trong `HomeworkEntity` và các DTO (`HomeworkCreate`, `HomeworkUpdate`, `HomeworkResponse`).
- **FR-003**: Hệ thống PHẢI cung cấp file migration Alembic để DROP bảng `homework_teams` khỏi cơ sở dữ liệu.
- **FR-004**: Hệ thống PHẢI loại bỏ toàn bộ các class domain entity và DTO legacy: `HomeworkSubmission`, `HomeworkSubmissionCreate`, `HomeworkSubmissionUpdate`, `HomeworkSubmissionResponse`, và enum `HomeworkSubmissionPermission`.
- **FR-005**: Endpoint `GET /homeworks/{id}/submission-status` PHẢI duy trì hoạt động thông qua `GetHomeworkSubmissionStatusUseCase` và DTO `HomeworkSubmissionStatusResponse` đối soát trực tiếp từ Quiz API.
- **FR-006**: `CheckOverdueHomeworkUseCase` PHẢI lấy danh sách người cần làm bài trực tiếp từ `assignee_ids` và loại bỏ hoàn toàn tham chiếu/inject `TeamRepository`.
- **FR-007**: Mỗi Use Case trong domain `Homework` PHẢI được tách thành một file độc lập trong thư mục `app/homework/application/` và re-export qua `__init__.py`.
- **FR-008**: Toàn bộ hệ thống test suite cho Homework và Typecheck (`make typecheck`) PHẢI vượt qua 100% không có lỗi.

---

### Key Entities *(include if feature involves data)*

- **Bài tập (`Homework`)**: Thực thể bài tập gồm: `id`, `title`, `deadline`, `link`, `slug`, `assignee_ids`, `created_at`, `updated_at`, `created_by`, `updated_by`, `is_deleted`.
- **Phân công bài tập (`HomeworkAssigneeModel`)**: Bảng `homework_assignees` lưu mapping giữa `homework_id` và `user_id`.
- **Trạng thái nộp bài (`HomeworkSubmissionStatusResponse`)**: Schema trả về tiến độ nộp bài Coding / Game của từng thành viên trong `assignee_ids` dựa trên dữ liệu thời gian thực từ Quiz API.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các API tạo, cập nhật, xem chi tiết và kiểm tra deadline bài tập hoạt động chính xác với `assignee_ids` không còn phụ thuộc vào bảng `homework_teams`.
- **SC-002**: Bảng `homework_teams` và model `HomeworkTeamModel` được xóa bỏ hoàn toàn (0 tham chiếu trong toàn bộ codebase).
- **SC-003**: Toàn bộ các class legacy `HomeworkSubmission` được dọn sạch khỏi domain Homework.
- **SC-004**: Tỷ lệ Pass của bộ kiểm thử tự động (Unit Tests) và kiểm tra kiểu dữ liệu tĩnh (`ty check`) đạt **100%** (0 lỗi).
- **SC-005**: 100% Use Cases trong domain Homework được chia tách theo cấu trúc 1 file / 1 class và export qua `__init__.py`.

---

## Assumptions

- Phía Giao diện Người dùng (UI / Frontend) sẽ tự thực hiện việc lấy danh sách thành viên từ các Team được chọn và gửi danh sách `assignee_ids` tổng hợp về Backend khi tạo/sửa bài tập.
- Dữ liệu lịch sử phân công bài tập trong `homework_assignees` đã có sẵn đầy đủ dữ liệu người dùng.
- Quiz API tiếp tục là nguồn chân lý (Source of Truth) duy nhất cho việc kiểm tra trạng thái nộp bài tập Coding và Game.
