# Feature Specification: Tách Biệt Các Repository Trong Module Homework & Tối Ưu SQL Join Cho Assignee

**Feature Branch**: `015-modular-homework-repositories`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "Tôi mong muốn tách các repo thành các class khác nhau nữa, định nghĩa ở các file khác nhau chứ ko phải gộp chung vào homework repo /speckit-specify"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tách Biệt Các Repository Đơn Nhiệm Trong Module Homework (Priority: P1)

Là một lập trình viên backend, tôi muốn các thao tác dữ liệu được tách thành các Repository độc lập theo đúng thực thể/bảng dữ liệu (`HomeworkRepository`, `HomeworkSubmissionRepository`, `HomeworkAssigneeRepository`), định nghĩa ở các file riêng biệt thay vì gom chung hơn 400 dòng vào một file duy nhất `repository.py`, giúp mã nguồn tầng Infrastructure tuân thủ Single Responsibility Principle và Clean Architecture.

**Why this priority**: File `repository.py` hiện tại là "God Repository" ôm đồm cả 3 bảng (`homeworks`, `homework_submissions`, `homework_assignees`), dẫn đến phình to và vi phạm ranh giới thực thể.

**Independent Test**: Có thể kiểm thử độc lập bằng cách inject từng Repository riêng biệt vào các Use Case tương ứng (`GetUserHomeworksUseCase`, `RecordHomeworkSubmissionUseCase`), kiểm tra CRUD bài tập và bài nộp hoạt động trơn tru.

**Acceptance Scenarios**:

1. **Given** một Use Case chỉ làm việc với bài nộp (`HomeworkSubmission`), **When** Use Case inject `HomeworkSubmissionRepository`, **Then** nó có thể thêm, cập nhật, tìm kiếm bài nộp mà không cần phụ thuộc vào logic CRUD bài tập.
2. **Given** một Use Case quản lý danh sách phân công (`HomeworkAssignee`), **When** hệ thống cần truy vấn hoặc gán học viên, **Then** `HomeworkAssigneeRepository` thực hiện các thao tác gán/lọc độc lập.

---

### User Story 2 - Tối Ưu Truy Vấn Lọc Bài Tập Bằng SQL JOIN Trực Tiếp (Priority: P2)

Là một học viên mở trang danh sách bài tập của mình (`/dashboard/my-homeworks`), tôi muốn hệ thống truy vấn và phân trang trực tiếp từ database bằng phép `JOIN` giữa bảng `homeworks` và `homework_assignees`, thay vì kéo 1000 bài tập về RAM rồi lọc thủ công bằng vòng lặp Python, giúp trang tải tức thì và không bị mất dữ liệu.

**Why this priority**: Khắc phục triệt để anti-pattern fetch-all in-memory filtering, cải thiện hiệu năng truy vấn từ $O(N)$ bộ nhớ xuống $O(1)$ tại tầng Database.

**Independent Test**: Kiểm tra query log hoặc gọi endpoint `GET /api/v1/homeworks/me` và `GET /api/v1/homeworks/report/unsubmitted/{user_id}`, thời gian phản hồi dưới 100ms và dữ liệu phân trang chuẩn xác.

**Acceptance Scenarios**:

1. **Given** học viên có 5 bài tập được giao trong tổng số 500 bài tập của hệ thống, **When** học viên gọi API lấy bài tập của mình, **Then** Database chỉ trả về đúng 5 bài tập thông qua `JOIN homework_assignees`, không duyệt qua 495 bài tập còn lại trong RAM.
2. **Given** hệ thống thống kê bài tập chưa nộp của học viên, **When** gọi `GetUnsubmittedHomeworksForUserUseCase`, **Then** danh sách bài tập được giao được lấy trực tiếp qua `HomeworkAssigneeRepository` hoặc `HomeworkRepository.get_assigned_to_user(...)` bằng SQL JOIN.

---

### User Story 3 - Cập Nhật Dishka Provider & Xóa Bỏ File Repository Gộp Cũ (Priority: P3)

Là một lập trình viên duy trì dự án, tôi muốn `HomeworkModuleProvider` đăng ký riêng từng Repository, các Use Case được cập nhật dependency trực tiếp, và file `repository.py` cũ được dọn dẹp sạch sẽ (không để alias thừa theo Nguyên tắc X của Constitution).

**Why this priority**: Đảm bảo toàn bộ ứng dụng chạy ổn định, không có code mồ côi hay alias rác.

**Independent Test**: Chạy toàn bộ test suite `pytest backend/tests/api/test_homework_api.py -v`, đạt 30/30 passed.

**Acceptance Scenarios**:

1. **Given** ứng dụng khởi động, **When** Dishka container xây dựng dependency graph, **Then** tất cả các Repository (`HomeworkRepository`, `HomeworkSubmissionRepository`, `HomeworkAssigneeRepository`) được resolve thành công ở `Scope.REQUEST`.
2. **Given** các test API bài tập chạy, **When** thực thi các kịch bản nộp bài, đồng bộ và xem báo cáo, **Then** 100% tests pass mà không phát sinh lỗi gãy tham chiếu.

---

### Edge Cases

- Khi một bài tập không có assignee nào (bài tập chung hoặc chưa gán): SQL JOIN với `homework_assignees` không trả về bài tập đó cho cá nhân (đúng theo logic bài tập được giao).
- Khi bài tập bị xóa mềm (`is_deleted = True`): Các truy vấn JOIN vẫn phải lọc chặt chẽ `HomeworkModel.is_deleted == False`.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST tách `repository.py` thành 3 tệp Repository riêng biệt trong thư mục `backend/app/homework/infrastructure/`:
  - `homework_repository.py`: Chuyên trách bảng `homeworks` (CRUD bài tập, phân trang, slug lookup, restore, soft delete).
  - `homework_submission_repository.py`: Chuyên trách bảng `homework_submissions` (CRUD bài nộp, tìm kiếm bài nộp theo bài/user, audit history, kiểm tra submission hợp lệ).
  - `homework_assignee_repository.py`: Chuyên trách bảng `homework_assignees` (truy vấn danh sách assignee, lấy danh sách homework_id của user bằng SQL JOIN, thêm/xóa assignee).
- **FR-002**: Hệ thống MUST thay thế toàn bộ logic in-memory filtering `[hw for hw in all_homeworks if user_id in hw.assignee_ids]` bằng truy vấn SQL JOIN trực tiếp tại Database.
- **FR-003**: `GetUserHomeworksUseCase` MUST sử dụng phương thức phân trang trực tiếp từ SQL (`LIMIT` / `OFFSET`) của Repository thay vì slice mảng 1000 phần tử trên Python RAM.
- **FR-004**: Hệ thống MUST cập nhật `backend/app/homework/infrastructure/__init__.py` để re-export 3 repository mới.
- **FR-005**: Hệ thống MUST cập nhật `backend/app/homework/providers.py` để cung cấp cả 3 repository trong Dishka container.
- **FR-006**: Hệ thống MUST cập nhật tất cả Use Case đang dùng các method submission/assignee sang inject đúng Repository chuyên biệt (`HomeworkSubmissionRepository` / `HomeworkAssigneeRepository`).
- **FR-007**: Hệ thống MUST xóa bỏ tệp `backend/app/homework/infrastructure/repository.py` cũ sau khi refactor hoàn tất.

### Key Entities

- **Homework**: Thực thể bài tập (`homeworks`).
- **HomeworkSubmission**: Thực thể bài nộp (`homework_submissions`).
- **HomeworkAssignee**: Thực thể liên kết phân công học viên (`homework_assignees`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tệp nguyên khối `repository.py` (405 dòng) được thay thế hoàn toàn bằng 3 tệp repository chuyên biệt, mỗi tệp phụ trách đúng 1 model/bảng dữ liệu.
- **SC-002**: Loại bỏ 100% việc fetch 1000 bản ghi về RAM để lọc bài tập trong `GetUserHomeworksUseCase` và `GetUnsubmittedHomeworksForUserUseCase`.
- **SC-003**: 30/30 backend tests trong `test_homework_api.py` pass 100%.
- **SC-004**: Thời gian phản hồi của endpoint `/api/v1/homeworks/me` được tối ưu hóa ở tầng DB thông qua index.

## Assumptions

- Việc tách repository không thay đổi cấu trúc bảng cơ sở dữ liệu hay Alembic migrations.
- API response contract và URL endpoint giữ nguyên vẹn 100%.
