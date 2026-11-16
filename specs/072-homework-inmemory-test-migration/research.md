# Research: In-Memory Fake Test Migration for Homework Module

**Feature**: `072-homework-inmemory-test-migration`  
**Date**: 2026-11-16  
**Status**: Completed  

---

## Technical Decisions

### Decision 1: Shared Fixtures vs Per-File In-Memory Fixtures

- **Context**: Hiện tại `test_homework_in_memory_use_cases.py` đang khai báo các fixtures: `homework_repo`, `submission_repo`, `assignee_repo`, `fake_quiz_api`, `spy_event_bus`. Khi chuyển đổi tất cả các file test khác (`test_homework_checker.py`, `test_homework_validation.py`, `test_homework_ssot.py`, `test_homework_scanner.py`, `test_homework_max_deadline_rule.py`), ta cần quyết định cách chia sẻ các fixture này.
- **Decision**: Tạo file fixture dùng chung `backend/tests/fixtures/homework_fixtures.py` và re-export trong `backend/tests/conftest.py` (hoặc cấu trúc pytest fixture modular). 
- **Rationale**: 
  - Tránh lặp lại mã khởi tạo `InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, `InMemoryHomeworkAssigneeRepository`, `FakeQuizApiClient`, và `SpyEventBus` ở 6 file test khác nhau.
  - Mỗi test function nhận một instance sạch (fresh instance) qua pytest fixture scope mặc định (`scope="function"`), đảm bảo tính độc lập tuyệt đối giữa các test case (zero test bleed / zero shared mutable state).
- **Alternatives considered**:
  - *Khai báo lặp lại trong từng file test*: Gây trùng lặp mã nguồn (DRY violation) và khó đồng bộ khi cập nhật interface của In-Memory Fake.

---

### Decision 2: Strategy for Migrating `test_homework_checker.py`

- **Context**: [`test_homework_checker.py`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/tests/unit/test_homework_checker.py) có 8 test functions với 531 dòng code sử dụng dày đặc `MagicMock()` cho `homework_repo`, `submission_repo`, `assignee_repo`, `event_bus`, `quiz_api`.
- **Decision**: Refactor trực tiếp toàn bộ 8 test functions trong `test_homework_checker.py` sang dùng In-Memory Repositories và SpyEventBus, giữ nguyên tên hàm và kịch bản nghiệp vụ.
- **Rationale**:
  - Giữ nguyên tên hàm (`test_check_overdue_homework_publishes_event`, `test_check_overdue_multi_exercise_partial_submission_flags_overdue`, v.v.) giúp các công cụ CI/CD, báo cáo kiểm thử và git blame dễ dàng theo dõi.
  - Thay vì mock `return_value` hay `side_effect`, ta seed dữ liệu thực vào `InMemoryHomeworkRepository`, `InMemoryHomeworkAssigneeRepository`, và `InMemoryHomeworkSubmissionRepository`.
  - Kết quả kiểm tra dựa trên trạng thái thật (state verification) và sự kiện được thu thập bởi `SpyEventBus`.
- **Alternatives considered**:
  - *Tạo file mới rồi xóa file cũ*: Mất lịch sử git blame và có nguy cơ bỏ sót kịch bản so với file gốc.

---

### Decision 3: Strategy for Validation, SSOT, and Scanner Tests

- **Context**: 
  - `test_homework_validation.py` test `CreateHomeworkUseCase` và `UpdateHomeworkUseCase`.
  - `test_homework_ssot.py` test `HomeworkExerciseResolver` và `GetHomeworkSubmissionStatusUseCase`.
  - `test_homework_scanner.py` test `RescanAllHomeworksUseCase`.
  - `test_homework_max_deadline_rule.py` (Test case 4) test `UpdateHomeworkUseCase` bảo vệ deadline cá nhân.
- **Decision**:
  - Thay toàn bộ `mock_homework_repo`, `mock_assignee_repo`, `mock_sub_repo` bằng In-Memory Fakes.
  - Với `test_homework_validation.py`: Lưu entity thật vào `InMemoryHomeworkRepository` và kiểm tra `repo.get_by_id(id)` hoặc `repo.get_by_slug(slug)` để xác nhận lưu thành công.
  - Với `test_homework_scanner.py`: Cung cấp `InMemoryHomeworkRepository`, `InMemoryHomeworkSubmissionRepository`, `InMemoryHomeworkAssigneeRepository` và `FakeUserRepository` (hoặc mock nhẹ User nếu User module chưa có In-Memory).
  - Với `test_homework_max_deadline_rule.py`: Kiểm tra `assignee_repo.get_user_deadline(...)` thực tế trong RAM thay vì `assignee_repo.assign_users.assert_called_once_with(...)`.
- **Rationale**: Kiểm thử dựa trên state thật (State-based Testing) chứng minh hệ thống hoạt động đúng bản chất nghiệp vụ chứ không chỉ đơn thuần là "gọi đúng hàm".

---

### Decision 4: External Boundaries (Quiz API & Notifications) Isolation

- **Context**: Có nên loại bỏ cả Mock cho `QuizApiClient` và `EventBus` không?
- **Decision**: Giữ nguyên hoặc chuẩn hóa thành `FakeQuizApiClient` và `SpyEventBus`. KHÔNG gọi HTTP ra ngoài và KHÔNG gửi message thật đến Telegram/Zalo.
- **Rationale**:
  - Theo nguyên tắc Hexagonal Architecture: Repository lưu trữ dữ liệu nội bộ (Database) phải dùng In-Memory Fake; còn các hệ thống bên ngoài mạng (Third-party External APIs) được cô lập bằng Test Doubles (Fake Client hoặc Stub).
  - `FakeQuizApiClient` phản hồi danh sách bài tập cố định trong RAM, giúp kiểm thử nhanh, không phụ thuộc vào kết nối mạng internet.
