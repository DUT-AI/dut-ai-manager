# Tasks: Đồng bộ và Thống nhất Trạng thái Hoàn thành Bài tập giữa Học viên và Quản lý

**Input**: Design documents from `/specs/069-unify-homework-submission-status/`  
**Prerequisites**: [plan.md](./plan.md) (required), [spec.md](./spec.md) (required), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/api_contract.md](./contracts/api_contract.md), [quickstart.md](./quickstart.md)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (`[US1]`, `[US2]`, `[US3]`)
- Every task includes exact file paths

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Chuẩn bị môi trường và kiểm tra cấu trúc nhánh làm việc

- [X] T001 Xác minh nhánh làm việc `069-unify-homework-submission-status` và trạng thái git repository
- [X] T002 [P] Khởi tạo tệp kiểm thử mới cho use case danh sách bài tập học viên tại `backend/tests/unit/test_get_user_homeworks.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Cơ sở hạ tầng Domain, Value Objects, Repository và DTOs bắt buộc hoàn thành trước khi triển khai các User Story

**⚠️ CRITICAL**: Các User Story không thể triển khai cho đến khi hoàn thành các tác vụ trong giai đoạn này

- [X] T003 [P] Cập nhật Value Object `SubmissionEvaluation` trong `backend/app/homework/domain/value_objects.py` bổ sung các thuộc tính `coding_status: str = "NOT_SUBMITTED"`, `total_coding_required: int = 0`, `total_coding_completed: int = 0`
- [X] T004 Cập nhật Aggregate Root `Homework.evaluate_submissions` trong `backend/app/homework/domain/entity.py` chấp nhận tham số `required_exercise_ids: set[str] | None = None`, đối chiếu tập bài con yêu cầu, tính toán `coding_status` ("COMPLETED", "PARTIALLY_SUBMITTED", "NOT_SUBMITTED") và cập nhật `uncompleted_items`
- [X] T005 [P] Thêm phương thức truy vấn tối ưu `get_required_exercise_ids_map(homework_ids: list[int]) -> dict[int, set[str]]` trong `backend/app/homework/infrastructure/homework_submission_repository.py` để trích xuất danh mục mã bài tập coding con từ SQL database
- [X] T006 [P] Cập nhật DTO `HomeworkResponse` trong `backend/app/homework/application/dtos.py` bổ sung các trường `coding_status: str = "NOT_SUBMITTED"`, `total_coding_required: int = 0`, `total_coding_completed: int = 0`
- [X] T007 [P] Cập nhật interface `Homework` trong `frontend/src/features/homework/types/homework.types.ts` bổ sung các trường `coding_status`, `total_coding_required`, `total_coding_completed`

**Checkpoint**: Nền tảng Domain, Repository, DTO và Frontend Types đã sẵn sàng - có thể tiến hành triển khai User Story 1 (MVP)

---

## Phase 3: User Story 1 - Học viên nhìn thấy chính xác trạng thái bài tập đang làm dở (Priority: P1) 🎯 MVP

**Goal**: Hiển thị chính xác trạng thái làm dở (`PARTIALLY_SUBMITTED`), tiến độ $K/N$ bài con trên thẻ bài tập của học sinh, ngăn ngừa ngộ nhận hoàn thành 100%.

**Independent Test**: Giao bài tập có 2 bài coding con, học viên nộp 1 bài. Trang "Bài tập của tôi" hiển thị thẻ viền màu hổ phách/cam (Amber) kèm tag `1/2 bài tập coding`, không hiển thị tích xanh "Đã nộp".

### Tests for User Story 1 ⚠️

- [X] T008 [P] [US1] Bổ sung unit test cho `evaluate_submissions` với trường hợp bài tập có nhiều bài con và nộp dở một phần trong `backend/tests/unit/test_homework_validation.py`
- [X] T009 [P] [US1] Viết unit test cho `GetUserHomeworksUseCase` kiểm tra kết quả trả về `is_submitted=False`, `coding_status="PARTIALLY_SUBMITTED"` khi học sinh chưa nộp đủ bài con trong `backend/tests/unit/test_get_user_homeworks.py`

### Implementation for User Story 1

- [X] T010 [US1] Cập nhật `GetUserHomeworksUseCase.execute` trong `backend/app/homework/application/get_user_homeworks_use_case.py` gọi `homework_submission_repo.get_required_exercise_ids_map`, truyền `required_exercise_ids` vào `hw.evaluate_submissions`, và gán đầy đủ `coding_status`, `total_coding_required`, `total_coding_completed` vào `HomeworkResponse`
- [X] T011 [US1] Cập nhật `HomeworkCard.tsx` trong `frontend/src/features/homework/components/HomeworkCard.tsx` xử lý trạng thái `isPartial` (viền trái màu cam `from-amber-400 to-orange-500`, icon cảnh báo, Tag hiển thị tiến độ `K/N bài con`, tooltip các mục chưa nộp)
- [X] T012 [US1] Rà soát và đồng bộ hiển thị trạng thái tại `frontend/src/features/homework/pages/MyHomeworkDetailPage.tsx` đảm bảo thống nhất câu chữ và trạng thái với thẻ bài tập bên ngoài

**Checkpoint**: User Story 1 đã hoàn thiện độc lập và có thể chạy thử nghiệm MVP

---

## Phase 4: User Story 2 - Thống nhất tiêu chí đánh giá giữa Giao diện Học viên và Giao diện Quản lý (Priority: P2)

**Goal**: Đảm bảo toàn bộ hệ thống (danh sách chưa nộp của cá nhân, báo cáo quản lý, bộ lọc tab) coi bài tập làm dở là "Chưa hoàn thành", khớp 100% với màn hình Quản lý bài tập.

**Independent Test**: Khi học sinh làm dở 1/2 bài con, bài tập phải nằm trong tab "Chưa nộp" của `MyHomeworkPage`, xuất hiện trong API `/api/v1/homework/unsubmitted`, và được đếm vào báo cáo `/api/v1/homework/reports/unsubmitted`.

### Implementation for User Story 2

- [X] T013 [P] [US2] Cập nhật `GetUnsubmittedHomeworksForUserUseCase` trong `backend/app/homework/application/get_unsubmitted_homeworks_for_user_use_case.py` lấy `required_exercise_ids` để các bài làm dở không bị loại nhầm khỏi danh sách chưa nộp
- [X] T014 [P] [US2] Cập nhật `GetUnsubmittedHomeworkReportUseCase` trong `backend/app/homework/application/get_unsubmitted_homework_report_use_case.py` lấy `required_exercise_ids` để báo cáo quản lý tính chính xác các bài tập học sinh mới làm dở vào `unsubmitted_count`
- [X] T015 [US2] Cập nhật bộ lọc và phân loại tab trong `frontend/src/features/homework/pages/MyHomeworkPage.tsx`: Tab "Chưa nộp" giữ lại bài làm dở (`!hw.isSubmitted`), Tab "Đã nộp" chỉ giữ bài hoàn thành 100% (`hw.isSubmitted === true`), cập nhật bộ đếm thống kê `stats`

**Checkpoint**: User Stories 1 và 2 đều hoạt động đồng bộ và thống nhất 100% giữa Học viên và Quản lý

---

## Phase 5: User Story 3 - Hệ thống nhắc nhở và tự động cảnh báo ghi nhận chính xác bài tập làm dở (Priority: P3)

**Goal**: Trình quét nhắc nhở (`HomeworkTaskScanner`) phát hiện và nhắc nhở đúng các học sinh có bài tập sắp đến hạn mà vẫn còn làm dở.

**Independent Test**: Chạy `HomeworkTaskScanner.scan_pending_tasks` với học sinh làm 1/2 bài con trước deadline 24h, hệ thống phải tạo `ScannedCandidateTask` để gửi thông báo nhắc nhở.

### Tests for User Story 3 ⚠️

- [X] T016 [P] [US3] Bổ sung unit test cho `HomeworkTaskScanner` kiểm tra việc không bỏ qua học sinh có bài làm dở trong `backend/tests/unit/test_homework_scanner.py`

### Implementation for User Story 3

- [X] T017 [US3] Cập nhật `HomeworkTaskScanner.scan_pending_tasks` trong `backend/app/reminder/application/scanners/homework_scanner.py` phân giải `required_exercise_ids` và đánh giá qua `hw.evaluate_submissions`, chỉ bỏ qua nhắc nhở khi học sinh đã hoàn thành đủ 100%

**Checkpoint**: Cả 3 User Stories đều đã hoạt động độc lập và hoàn thiện trọn vẹn

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Kiểm thử hồi quy toàn diện, xác thực chất lượng mã nguồn và tài liệu

- [X] T018 [P] Chạy toàn bộ test suite của domain homework trong `backend/tests/unit/` (`pytest tests/unit/test_homework*.py -v`) đảm bảo không có bất kỳ regression nào
- [X] T019 [P] Chạy kiểm tra TypeScript và linter trên Frontend (`cd frontend && npm run build` hoặc `npm run type-check`)
- [X] T020 Thực hiện xác thực kịch bản end-to-end theo hướng dẫn trong [quickstart.md](./quickstart.md)

---

## Phase 7: Constitution Compliance & Pydantic V2 Refactoring (Priority: P1)

**Goal**: Triệt tiêu 100% duck-typing phòng thủ (`hasattr`) trên collaborator repository, chuyển đổi DTO sang đúng ranh giới kiến trúc, và nâng cấp Pydantic V2 sạch deprecation warnings theo đúng DUT AI Manager Constitution (Nguyên tắc I, VII, XIII, XIV, XVIII).

**Independent Test**:
- Không còn bất kỳ từ khóa `hasattr` nào truy cập `self.homework_submission_repo` trong `backend/app/homework/`, `backend/app/permission_request/`, `backend/app/reminder/`.
- `HomeworkSubmissionWebhookIn` nằm tại `backend/app/homework/application/dtos.py` và các bài test webhook/use case import hợp lệ.
- 100% unit tests (281/281 tests) pass mượt mà, `ruff check` đạt 0 lỗi cảnh báo.

### Implementation Tasks for Constitution & Pydantic V2 Refactoring

- [X] T021 [P] [Refactor] Di chuyển `HomeworkSubmissionWebhookIn` từ `backend/app/homework/application/record_submission_use_case.py` sang `backend/app/homework/application/dtos.py`, bổ sung vào `__all__` tại `backend/app/homework/application/__init__.py`, và cập nhật import tại `record_submission_use_case.py`, `backend/app/homework/controller.py`, `backend/tests/integration/test_homework_webhook.py`
- [X] T022 [P] [Refactor] Nâng cấp Pydantic V2 trong `backend/app/homework/application/dtos.py`: thay thế `class Config: from_attributes = True` bằng `model_config = ConfigDict(from_attributes=True)` trên `HomeworkResponse`, và refactor `parse_typed_details` loại bỏ `hasattr`
- [X] T023 [Refactor] Triệt tiêu duck-typing `hasattr` trong `backend/app/homework/application/check_overdue_homework_use_case.py` (loại bỏ 4 điểm `hasattr` tại dòng 75, 115, 122, 137, gọi trực tiếp các phương thức của `self.homework_submission_repo`)
- [X] T024 [P] [Refactor] Triệt tiêu duck-typing `hasattr` trong `backend/app/permission_request/application/strategies/postpone_strategy.py` (loại bỏ `hasattr` tại dòng 87, gọi trực tiếp `self.homework_submission_repo.get_required_exercise_ids_map`)
- [X] T025 [P] [Refactor] Triệt tiêu duck-typing `hasattr` trong `backend/app/reminder/application/scanners/homework_scanner.py` (loại bỏ `hasattr` tại dòng 41, gọi trực tiếp `self.homework_submission_repo.get_required_exercise_ids_map`)
- [X] T026 [Refactor] Cập nhật các mock object trong test suites (`backend/tests/unit/test_homework_checker.py`, `backend/tests/unit/test_homework_scanner.py`,...) để bảo đảm mọi test mock đều tuân thủ đầy đủ contract thực tế của `HomeworkSubmissionRepository`
- [X] T027 [Polish] Chạy toàn bộ test suites (`pytest backend/tests/unit/ -v` và `pytest backend/tests/integration/test_homework_webhook.py -v`), chạy `ruff check`, và chạy `npm run build` trên frontend để xác nhận zero regressions

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Hoàn thành
- **Foundational (Phase 2)**: Hoàn thành
- **User Story 1 (Phase 3)**: Hoàn thành
- **User Story 2 (Phase 4)**: Hoàn thành
- **User Story 3 (Phase 5)**: Hoàn thành
- **Polish (Phase 6)**: Hoàn thành
- **Constitution Compliance & Pydantic V2 Refactoring (Phase 7)**:
  - T021 & T022 có thể chạy song song [P].
  - T023, T024, T025 chạy song song [P].
  - T026 chạy sau T023, T024, T025 nếu có mock test nào thiếu method.
  - T027 là verification gate cuối cùng.

---

## Notes

- Toàn bộ 20/20 nhiệm vụ ban đầu đã hoàn thành. Phase 7 bổ sung 7 nhiệm vụ refactor chuyên sâu nhằm đảm bảo 100% tuân thủ Hiến chương dự án.
