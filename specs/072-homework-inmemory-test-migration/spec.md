# Feature Specification: Full In-Memory Fake Test Migration for Homework Module

**Feature Branch**: `072-homework-inmemory-test-migration`  
**Created**: 2026-11-16  
**Status**: Draft  
**Input**: Yêu cầu người dùng: "hãy chuyển toàn bộ các test case của module homework sang dùng hoàn toàn In-Memory Fake, sau đó xóa các mock cũ /speckit-plan"

---

## Background & Motivation

Feature `071-architecture-redesign` đã thiết lập thành công nền tảng Hexagonal Architecture (Ports & Adapters) và các In-Memory Fake Repositories (`InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, `InMemoryHomeworkAssigneeRepository`) cho module Homework.

Tuy nhiên, trong thư mục `backend/tests/unit/`, các file test unit cũ vẫn còn tồn đọng một lượng lớn `unittest.mock.MagicMock` gắn chặt vào hành vi giả lập (`mock.get_by_id.return_value = ...`, `side_effect = ...`, `assert_called_once_with(...)`). Các bài test này:
1. **Dễ vỡ (Brittle)**: Khi tái cấu trúc logic nội bộ của Use Case, mock dễ báo lỗi giả (false positive) hoặc bỏ lọt lỗi logic thật (false negative).
2. **Thiếu tính xác thực (State Fidelity)**: Không kiểm tra được dữ liệu lưu trữ thực tế trên bộ nhớ, không phản ánh đúng quan hệ giữa các bảng/aggregate.
3. **Gây khó khăn bảo trì**: Việc cấu hình mock lặp đi lặp lại hàng chục dòng code khiến test suite cồng kềnh, khó đọc.

Bản đặc tả này quy định việc **chuyển đổi toàn diện (100%)** các unit test cases trong module `homework` sang sử dụng In-Memory Fake Fixtures, kiểm thử dựa trên trạng thái thực tế (State & Behavior Testing), và xóa bỏ an toàn các file/test case mock cũ mà không làm suy giảm độ bao phủ kiểm thử (test coverage) hay gây hồi quy hệ thống.

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Migrate Checker & Scanner Test Suites to In-Memory Fakes (Priority: P1) 🎯 MVP

Là một Kỹ sư Kiểm thử và Đảm bảo Chất lượng,  
Tôi muốn toàn bộ các ca kiểm thử quét quá hạn ([`test_homework_checker.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_checker.py)) và quét toàn bộ bài tập ([`test_homework_scanner.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_scanner.py)) được chuyển sang thực thi trên In-Memory Fake Repositories,  
Để luồng quét bài nộp quá hạn chạy nhanh như chớp trên RAM, kiểm tra chính xác sự kiện miền `HomeworkOverdueDetected` mà không dùng bất kỳ `MagicMock` nào cho Database Repositories.

**Why this priority**: `test_homework_checker.py` là file test lớn nhất (hơn 530 dòng) chứa 8 kịch bản nghiệp vụ phức tạp với nhiều mock lồng nhau nhất. Đây là nguồn rủi ro và nợ kỹ thuật lớn nhất cần dọn dẹp trước.

**Independent Test**: Chạy test suite `test_homework_checker.py` (hoặc phiên bản in-memory tương đương) trong < 0.2s, 100% tests PASS, không có bất kỳ dòng lệnh `MagicMock(spec=...)` nào liên quan đến Repository.

**Acceptance Scenarios**:
1. **Given** bài tập có nhiều bài con, **When** học viên mới nộp một phần bài con trước hạn, **Then** Use Case phát hiện bài nộp dở dang và bắn sự kiện `HomeworkOverdueDetected` chính xác theo dữ liệu trong RAM.
2. **Given** học viên nộp bài sau deadline, **When** quét hạn, **Then** In-Memory Repository và Domain Entity phối hợp bỏ qua bài nộp muộn và ghi nhận quá hạn.
3. **Given** nhiều học viên có deadline cá nhân khác nhau (gia hạn), **When** quét hạn theo từng ngày, **Then** hệ thống xử lý độc lập từng học viên đúng theo bản ghi trong `InMemoryHomeworkAssigneeRepository`.
4. **Given** Quiz API gặp sự cố mạng, **When** quét hạn, **Then** hệ thống tự động fallback phân giải bài tập con từ các bài nộp đã lưu trong `InMemoryHomeworkSubmissionRepository`.

---

### User Story 2 - Migrate Validation & SSOT Test Suites to In-Memory Fakes (Priority: P2)

Là một Nhà phát triển Tính năng,  
Tôi muốn các ca kiểm thử xác thực tạo/sửa bài tập ([`test_homework_validation.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_validation.py)) và phân giải nguồn chân lý duy nhất ([`test_homework_ssot.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_ssot.py)) vận hành hoàn toàn trên In-Memory Fake Repositories,  
Để các luồng nghiệp vụ `CreateHomeworkUseCase`, `UpdateHomeworkUseCase`, `GetHomeworkSubmissionStatusUseCase` được xác minh lưu trữ và truy vấn trạng thái thực sự.

**Why this priority**: Đảm bảo các Use Case tạo mới và cập nhật bài tập tương tác chuẩn mực với Port, dữ liệu được nạp vào và lấy ra nhất quán từ `InMemoryHomeworkRepository`.

**Independent Test**: Chạy `test_homework_validation.py` và `test_homework_ssot.py`, kiểm tra entity được lưu thực tế trong `_storage` của In-Memory Repo thay vì `mock_repo.save.assert_called_once()`.

**Acceptance Scenarios**:
1. **Given** dữ liệu bài tập hợp lệ, **When** gọi `CreateHomeworkUseCase.execute()`, **Then** bài tập được tạo mới, lưu vào `InMemoryHomeworkRepository` với ID tự sinh và có thể truy vấn lại bằng `get_by_id` hoặc `get_by_slug`.
2. **Given** bài tập đã có trong `InMemoryHomeworkRepository`, **When** gọi `UpdateHomeworkUseCase.execute()` bỏ chọn game, **Then** cờ `requires_game` được cập nhật thành `False` trong RAM.
3. **Given** học viên có lịch sử nộp bài trong `InMemoryHomeworkSubmissionRepository`, **When** gọi `GetHomeworkSubmissionStatusUseCase.execute()`, **Then** trả về tiến độ chi tiết và số lượng hoàn thành chính xác 100%.

---

### User Story 3 - Migrate Max Deadline Rule & Safe Deletion of Obsolete Mock Tests (Priority: P3)

Là một Kiến trúc sư Hệ thống,  
Tôi muốn chuyển đổi bài test cập nhật deadline cá nhân trong [`test_homework_max_deadline_rule.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_max_deadline_rule.py) sang In-Memory Fake, sau đó xóa bỏ an toàn các test case/file mock cũ,  
Để codebase sạch sẽ, nhất quán, không còn mã nguồn thừa hay test giả lập dễ vỡ.

**Why this priority**: Hoàn tất chu trình dọn dẹp, đảm bảo module homework đạt tiêu chuẩn Zero-Mock cho tầng lưu trữ dữ liệu.

**Independent Test**: Kiểm tra toàn bộ thư mục `backend/tests/unit/test_homework_*.py` không còn bất kỳ dòng `from unittest.mock import MagicMock` nào dùng cho repositories, toàn bộ test suites tiếp tục PASS 100%.

**Acceptance Scenarios**:
1. **Given** học viên có hạn hoãn cá nhân, **When** gọi `UpdateHomeworkUseCase.execute(force_override_deadlines=False)`, **Then** `InMemoryHomeworkAssigneeRepository` bảo lưu nguyên vẹn hạn hoãn cá nhân của học sinh mà không cần kiểm tra mock calls.
2. **Given** các test case In-Memory đã bao phủ 100% kịch bản của file mock cũ, **When** tiến hành xóa bỏ các mock cũ, **Then** toàn bộ test suite của hệ thống vẫn PASS 100% không suy giảm coverage.

---

## Edge Cases

- **Fallback Exercise Resolution**: Khi `FakeQuizApiClient` trả về `None` hoặc raise Exception, Use Case phải fallback tự động xuống `InMemoryHomeworkSubmissionRepository.get_submissions_by_homework()` mà không bị crash.
- **External API Boundaries**: Giữ nguyên Mock/Fake tối giản cho các ranh giới ngoại vi (External Network boundaries) như `QuizApiClient` (mạng ngoài) và `EventBus`/`NotificationDispatcher` (bắn notification ra ngoài), chỉ tập trung xóa bỏ Mock của Database Repositories.
- **Database Session Isolation**: Các bài test integration (`tests/integration/test_homework_*.py`) kiểm tra tương tác cơ sở dữ liệu thật với SQLAlchemy Session vẫn được giữ nguyên để kiểm chứng tầng hạ tầng (Infrastructure verification).

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống kiểm thử unit của module homework PHẢI sử dụng `InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, và `InMemoryHomeworkAssigneeRepository` thay cho `MagicMock` của các Repository tương ứng.
- **FR-002**: Tất cả các kịch bản nghiệp vụ trong [`test_homework_checker.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_checker.py) PHẢI được di chuyển đầy đủ sang kiến trúc In-Memory với kết quả xác minh trạng thái (State verification) tương đương hoặc chặt chẽ hơn.
- **FR-003**: Kịch bản kiểm tra `UpdateHomeworkUseCase` trong [`test_homework_max_deadline_rule.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_max_deadline_rule.py) PHẢI được chuyển từ mock sang In-Memory Fake.
- **FR-004**: Toàn bộ mock repositories trong [`test_homework_scanner.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_scanner.py), [`test_homework_ssot.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_ssot.py), và [`test_homework_validation.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_validation.py) PHẢI được thay thế hoàn toàn bằng In-Memory Fakes.
- **FR-005**: Sau khi di chuyển và xác minh thành công, các test case hoặc file mock cũ PHẢI được dọn dẹp, đảm bảo linter Ruff 0 lỗi.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các bài test unit của module homework chạy thành công (PASS) mà không có bất kỳ mock nào cho `HomeworkRepository`, `HomeworkSubmissionRepository`, hay `HomeworkAssigneeRepository`.
- **SC-002**: Tốc độ thực thi của toàn bộ unit test suite `test_homework_*.py` đạt dưới 1.5 giây trên môi trường local.
- **SC-003**: Toàn bộ test suite hệ thống (467 tests backend) tiếp tục đạt tỷ lệ PASS 100%, không có bất kỳ hồi quy (regression) nào.
- **SC-004**: Kiểm tra mã nguồn bằng Ruff Linter trên `backend/tests/unit/` đạt 0 errors, 0 warnings.
