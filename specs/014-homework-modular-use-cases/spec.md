# Feature Specification: Tách Biệt Các Use Case Homework & Submission (Modular Use Cases) & Dọn Dẹp Code Rác

**Feature Branch**: `014-homework-modular-use-cases`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "tôi muốn tách ra các use case homework, submission riêng biệt thay vì gộp vào 1 file như thế này, hãy check thử trong module homework có những code rác nào ko? /speckit-specify"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tách Use Case Truy Vấn Bài Tập và Báo Cáo Riêng Biệt (Priority: P1)

Là một lập trình viên và quản trị viên hệ thống, tôi muốn các thao tác nghiệp vụ truy vấn bài tập (danh sách chung, bài tập của tôi, bài tập chưa nộp, báo cáo tổng hợp) được phân tách thành từng Use Case độc lập, mỗi Use Case chỉ có một phương thức thực thi chính (`execute`), tuân thủ triệt để Nguyên tắc VII của Constitution v1.5.0, giúp mã nguồn rõ ràng, dễ bảo trì và dễ viết unit test.

**Why this priority**: Lớp `GetHomeworksUseCase` hiện đang là "god class" chứa tới 6 phương thức khác nhau (`get_paged`, `get_all`, `get_by_id`, `get_assigned_to_user`, `get_unsubmitted_for_user`, `get_unsubmitted_report`), vi phạm nguyên tắc Single-Responsibility Use Case.

**Independent Test**: Có thể kiểm thử độc lập bằng cách gọi từng Use Case riêng biệt qua Dishka Dependency Injection và kiểm tra kết quả trả về khớp 100% với dữ liệu hiện tại, toàn bộ test suite cũ pass.

**Acceptance Scenarios**:

1. **Given** một yêu cầu lấy danh sách bài tập của cá nhân học viên, **When** hệ thống gọi `GetUserHomeworksUseCase.execute(user_id, pagination)`, **Then** danh sách bài tập kèm trạng thái nộp bài được tính toán chính xác từ database nội bộ và trả về đúng định dạng.
2. **Given** một yêu cầu lấy báo cáo thống kê bài tập chưa nộp của toàn bộ thành viên, **When** hệ thống gọi `GetUnsubmittedHomeworkReportUseCase.execute()`, **Then** danh sách thống kê xếp hạng số bài chưa nộp được trả về chính xác mà không phụ thuộc vào các logic phân trang bài tập khác.
3. **Given** một yêu cầu lấy chi tiết bài tập theo ID hoặc danh sách phân trang cho Admin, **When** hệ thống gọi `GetHomeworkDetailUseCase.execute(id)` hoặc `GetHomeworksPagedUseCase.execute(...)`, **Then** thông tin bài tập được truy xuất độc lập từ repository.

---

### User Story 2 - Dọn Dẹp Code Rác và Mã Nguồn Thừa Trong Module Homework (Priority: P2)

Là một kỹ sư phần mềm, tôi muốn loại bỏ các class rỗng không dùng đến (`HomeworkService` trong `domain/services.py`), các logic import thừa, và dịch vụ không còn được sử dụng (`HomeworkGradingService` trong `infrastructure/external_api.py`), giúp module gọn gàng và không gây nhầm lẫn khi phát triển tiếp.

**Why this priority**: Giữ cho codebase sạch sẽ, không có file "zombie" (file tồn tại nhưng không ai gọi hoặc class rỗng), tuân thủ tiêu chí Clean Code và Nguyên tắc I / X của Constitution.

**Independent Test**: Sau khi xóa hoặc dọn dẹp các tệp/class rác, chạy `pytest` và kiểm tra toàn bộ project không có bất kỳ import warning hoặc gãy dependency nào.

**Acceptance Scenarios**:

1. **Given** tệp `backend/app/homework/domain/services.py` chỉ có `class HomeworkService: pass` không ai dùng, **When** tiến hành dọn dẹp, **Then** loại bỏ class thừa này hoặc biến nó thành Domain Service thực thụ nếu cần logic tính toán submission, đồng thời loại bỏ các import không sử dụng.
2. **Given** tệp `backend/app/homework/infrastructure/external_api.py` chứa `HomeworkGradingService` không còn nơi nào trong backend gọi đến, **When** rà soát mã nguồn rác, **Then** loại bỏ hoặc refactor để tránh duplicate API surface.

---

### User Story 3 - Cập Nhật Nhà Cung Cấp Dishka và Controller Tương Thích Hoàn Toàn (Priority: P3)

Là một lập trình viên duy trì hệ thống, tôi muốn `providers.py` và `controller.py` inject trực tiếp các Use Case đơn nhiệm cụ thể, cập nhật router endpoint trực tiếp tại call sites (kể cả module `report` đang phụ thuộc vào `GetHomeworksUseCase`), đảm bảo hệ thống khởi chạy trơn tru, không có runtime crash.

**Why this priority**: Đảm bảo toàn bộ ứng dụng (FastAPI routers, Report domain) chuyển đổi sang kiến trúc Use Case mới một cách an toàn và bền vững.

**Independent Test**: Chạy `backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v` và các test của module report, tất cả đều pass 100%.

**Acceptance Scenarios**:

1. **Given** router `/homeworks/me` và `/homeworks/report/unsubmitted`, **When** client gửi request, **Then** FastAPI inject chính xác `GetUserHomeworksUseCase` và `GetUnsubmittedHomeworkReportUseCase` và trả về kết quả thành công HTTP 200.
2. **Given** module `report/application/use_cases.py` đang dùng `GetHomeworksUseCase.get_unsubmitted_for_user`, **When** tái cấu trúc, **Then** module report được cập nhật trực tiếp sang inject Use Case chuyên trách `GetUnsubmittedHomeworksForUserUseCase` (hoặc tên tương đương).

---

### Edge Cases

- Khi một Use Case cần dữ liệu của cả bài tập và bài nộp: Use Case chuyên trách sẽ inject `HomeworkRepository` và `UserRepository`, thực hiện orchestration trực tiếp mà không lặp lại mã nguồn phân tích bài nộp.
- Khi module `report` cần thống kê bài tập chưa nộp của một user: Việc đổi dependency không làm hỏng tính toán Dashboard Overview của report.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống MUST phân tách `GetHomeworksUseCase` thành các Use Case chuyên biệt:
  - `GetHomeworksPagedUseCase`: Lấy danh sách bài tập phân trang cho trang quản trị (`GET /homeworks`).
  - `GetHomeworkDetailUseCase`: Lấy chi tiết một bài tập theo ID (`GET /homeworks/{id}`).
  - `GetUserHomeworksUseCase`: Lấy danh sách bài tập được giao cho học viên hiện tại (`GET /homeworks/me`).
  - `GetUnsubmittedHomeworksForUserUseCase`: Lấy danh sách bài tập chưa nộp của một học viên (`GET /homeworks/report/unsubmitted/{user_id}`).
  - `GetUnsubmittedHomeworkReportUseCase`: Thống kê tổng hợp số bài tập chưa nộp của tất cả học viên (`GET /homeworks/report/unsubmitted`).
- **FR-002**: Mỗi Use Case mới MUST chỉ chứa một phương thức công khai duy nhất `execute(...)`, đặt trong tệp riêng biệt theo quy chuẩn `*_use_case.py`.
- **FR-003**: Hệ thống MUST dọn dẹp các tệp/mã nguồn rác được xác định trong module `homework`:
  - `backend/app/homework/domain/services.py` (hiện tại rỗng `class HomeworkService: pass`).
  - `backend/app/homework/infrastructure/external_api.py` (chứa `HomeworkGradingService` không được sử dụng ở bất kỳ đâu).
  - Xóa bỏ file `get_homeworks_use_case.py` sau khi phân tách xong.
- **FR-004**: Hệ thống MUST cập nhật tệp `backend/app/homework/application/__init__.py` để re-export đầy đủ các Use Case mới theo danh sách `__all__`.
- **FR-005**: Hệ thống MUST cập nhật `backend/app/homework/providers.py` và `backend/app/report/providers.py` để đăng ký các Use Case mới vào Dishka container.
- **FR-006**: Hệ thống MUST cập nhật `backend/app/homework/controller.py` và `backend/app/report/application/use_cases.py` trực tiếp tại call sites, không sử dụng alias tương thích ngược thừa thãi (tuân thủ Nguyên tắc X của Constitution).

### Key Entities

- **Homework**: Thực thể bài tập (Domain Entity: tiêu đề, hạn nộp, link, slug, cờ `requires_coding`, `requires_game`, danh sách assignee).
- **HomeworkSubmission**: Thực thể bài nộp của học viên (Audit log: `homework_id`, `user_id`, `submission_type`, `submitted_at`, `is_passed`, `score`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: File `get_homeworks_use_case.py` được thay thế hoàn toàn bằng 5 file Use Case đơn nhiệm, mỗi file < 120 dòng code, đạt 100% tuân thủ Single-Responsibility Principle.
- **SC-002**: Xóa bỏ thành công 100% code rác (`HomeworkService` rỗng, `HomeworkGradingService` mồ côi) trong module `homework`.
- **SC-003**: Toàn bộ test suite liên quan (`backend/tests/api/test_homework_api.py`) đạt 30/30 passed với thời gian thực thi ổn định.
- **SC-004**: Frontend và Zalo Mini App hoạt động trơn tru 100%, không bị ảnh hưởng do API request/response schema được giữ nguyên vẹn.

## Assumptions

- Việc phân tách Use Case chỉ tổ chức lại lớp Application của Backend, không thay đổi đường dẫn URL, method HTTP hay cấu trúc request/response của các API endpoint hiện tại.
- Các module khác (như `report`) gọi logic bài tập chưa nộp sẽ được chuyển sang inject Use Case chuyên trách tương ứng thay vì Use Case gộp.
