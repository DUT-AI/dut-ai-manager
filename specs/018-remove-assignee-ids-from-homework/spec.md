# Feature Specification: Loại Bỏ `assignee_ids` Khỏi Entity `Homework`

**Feature Branch**: `018-remove-assignee-ids-from-homework`

**Created**: 2026-10-19

**Status**: Draft

**Input**: User description: "hãy bỏ assignee_ids: list[int] = [] khỏi homework cho tôi"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Khởi Tạo & Truy Vấn Bài Tập Tinh Gọn (Priority: P1)

Là một lập trình viên hoặc thành viên hệ thống, tôi muốn thực thể `Homework` (Aggregate Root) thuần túy chứa thông tin bài tập (tiêu đề, deadline, link, slug, cờ bài tập) mà không phải gánh vác danh sách ID học sinh (`assignee_ids`), giúp giảm thiểu tài nguyên bộ nhớ và loại bỏ phụ thuộc dữ liệu N-N không cần thiết trong Aggregate Root.

**Why this priority**: Đây là mục tiêu cốt lõi của việc tái cấu trúc theo Clean Architecture & DDD. Tách biệt hoàn toàn quan hệ phân công bài tập sang `HomeworkAssigneeRepository`.

**Independent Test**:
- Kiểm tra khởi tạo `Homework(...)` không nhận hoặc không yêu cầu `assignee_ids`.
- Kiểm tra các hàm `HomeworkRepository.get_by_id`, `get_all` trả về thực thể `Homework` độc lập, không join tải dư thừa `assignees`.

**Acceptance Scenarios**:
1. **Given** Entity `Homework`, **When** khởi tạo bài tập mới, **Then** không tồn tại thuộc tính `assignee_ids` trên `Homework`.
2. **Given** Database có bài tập được gán cho nhiều học sinh, **When** gọi `homework_repo.get_by_id(homework_id)`, **Then** trả về `Homework` sạch sẽ không chứa mảng user IDs.

---

### User Story 2 - Quản Lý Phân Công Bài Tập Qua `HomeworkAssigneeRepository` (Priority: P2)

Là một quản trị viên (Admin/Trainer), khi tôi tạo mới hoặc cập nhật bài tập cùng danh sách học sinh được giao, hệ thống vẫn lưu trữ và đồng bộ hóa chính xác danh sách phân công học sinh vào bảng `homework_assignees` thông qua `HomeworkAssigneeRepository`.

**Why this priority**: Đảm bảo chức năng quản lý bài tập không bị gián đoạn hay mất dữ liệu phân công học viên.

**Independent Test**:
- Gọi API `POST /api/v1/homeworks` và `PUT /api/v1/homeworks/{id}` với `assignee_ids`.
- Xác minh dữ liệu trong bảng `homework_assignees` được đồng bộ chính xác qua `homework_assignee_repo.get_assigned_user_ids(homework_id)`.

**Acceptance Scenarios**:
1. **Given** DTO tạo bài tập có `assignee_ids = [1, 2]`, **When** `CreateHomeworkUseCase.execute()` được gọi, **Then** bài tập được tạo và `homework_assignee_repo.sync_assignees` được gọi để lưu 2 học viên này.
2. **Given** Bài tập hiện tại, **When** `UpdateHomeworkUseCase.execute()` cập nhật `assignee_ids = [3]`, **Then** bảng `homework_assignees` được đồng bộ chính xác chỉ còn user 3.

---

### User Story 3 - Duy Trì Đầy Đủ Logic Các Báo Cáo & Cron Job Quá Hạn (Priority: P3)

Là một quản trị viên hoặc hệ thống kiểm tra tự động (cron job), khi chạy kiểm tra bài tập quá hạn (`CheckOverdueHomeworkUseCase`) hoặc thống kê bài tập chưa nộp (`GetUnsubmittedHomeworkReportUseCase`), hệ thống lấy danh sách học sinh được phân công từ `HomeworkAssigneeRepository` và xử lý thông suốt.

**Why this priority**: Đảm bảo tính toàn vẹn của nghiệp vụ giám sát học viên và tính năng thông báo hạn chót.

**Independent Test**:
- Chạy unit test / integration test cho `CheckOverdueHomeworkUseCase` và `GetUnsubmittedHomeworkReportUseCase` đảm bảo tất cả test cases đều pass mà không phụ thuộc vào `homework.assignee_ids`.

**Acceptance Scenarios**:
1. **Given** Cron job kiểm tra quá hạn chạy, **When** duyệt qua danh sách bài tập đến hạn, **Then** truy vấn `homework_assignee_repo.get_assigned_user_ids(homework.id)` để xác định danh sách học sinh cần kiểm tra.
2. **Given** Báo cáo bài tập chưa nộp, **When** tổng hợp cho từng user, **Then** sử dụng danh sách phân công từ `HomeworkAssigneeRepository`.

---

### Edge Cases

- **Bài tập không phân công ai**: Khi tạo bài tập với `assignee_ids = []` hoặc `None`, `Homework` vẫn được tạo thành công và `homework_assignee_repo` không tạo bản ghi nào trong `homework_assignees`.
- **Cập nhật bài tập không truyền `assignee_ids`**: Nếu payload update không chỉ định `assignee_ids` (hoặc `None`), hệ thống giữ nguyên danh sách phân công hiện tại.
- **Xóa mềm / Khôi phục bài tập**: Việc xóa hoặc khôi phục bài tập không làm hỏng dữ liệu phân công trong `HomeworkAssigneeRepository`.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Thực thể Domain `Homework` (`backend/app/homework/domain/entity.py`) MUST xóa bỏ trường `assignee_ids: list[int] = []`.
- **FR-002**: Tầng Infrastructure `HomeworkModel.to_entity()` (`backend/app/homework/infrastructure/model.py`) MUST không gán `assignee_ids` vào `Homework` entity.
- **FR-003**: `HomeworkRepository` MUST loại bỏ phương thức `sync_assignees` và logic phân công học sinh trong `create()` / `update()`; trách nhiệm này chuyển giao trọn vẹn cho `HomeworkAssigneeRepository`.
- **FR-004**: `CreateHomeworkUseCase` MUST nhận `assignee_ids` từ DTO và phối hợp cùng `HomeworkAssigneeRepository.sync_assignees(homework.id, data.assignee_ids)` để gán học viên.
- **FR-005**: `UpdateHomeworkUseCase` MUST kiểm tra nếu `data.assignee_ids` được cung cấp thì gọi `HomeworkAssigneeRepository.sync_assignees(homework_id, data.assignee_ids)`.
- **FR-006**: `CheckOverdueHomeworkUseCase` MUST sử dụng `HomeworkAssigneeRepository.get_assigned_user_ids(homework.id)` thay vì truy cập `homework.assignee_ids`.
- **FR-007**: `GetUnsubmittedHomeworkReportUseCase` và `GetUserHomeworksUseCase` MUST truy vấn dữ liệu phân công thông qua `HomeworkAssigneeRepository`.
- **FR-008**: DTOs (`HomeworkResponse`, `HomeworkDetailDTO`) và Controller endpoints MUST duy trì cấu trúc API hiện tại cho client nếu cần trả về danh sách phân công.

### Key Entities

- **Homework**: Thực thể gốc (Aggregate Root) đại diện cho đề bài tập, chỉ chứa thông tin: `id`, `title`, `deadline`, `link`, `slug`, `requires_coding`, `requires_game`.
- **HomeworkAssignee**: Bản ghi phân công học sinh cho bài tập, được quản lý độc lập bởi `HomeworkAssigneeRepository`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero references: Không còn bất kỳ đoạn mã nào truy cập `homework.assignee_ids` trên thực thể Domain `Homework`.
- **SC-002**: 100% Test Suite Passed: Toàn bộ 30+ tests trong `tests/api/test_homework_api.py`, `tests/unit/test_homework_*.py`, và `tests/integration/` đều pass sau khi refactor.
- **SC-003**: Không có breaking change trên HTTP API: Client gửi payload `assignee_ids` khi tạo/sửa bài tập vẫn hoạt động bình thường và response vẫn tương thích.

---

## Assumptions

- Việc phân công học viên vẫn được lưu tại bảng cơ sở dữ liệu `homework_assignees`.
- Bảng `homework_assignees` đã có index và đã có class `HomeworkAssigneeRepository` phụ trách các tác vụ này.
- Frontend không bị ảnh hưởng do API contract của DTO request/response vẫn được bảo toàn tại tầng Application/Presentation.
