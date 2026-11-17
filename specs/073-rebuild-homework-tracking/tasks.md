---

description: "Danh sách tác vụ triển khai cho tính năng Xây Dựng Lại Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập Học Viên"
---

# Tasks: Xây Dựng Lại Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập Học Viên

**Input**: Design documents từ `specs/073-rebuild-homework-tracking/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/api-contracts.md`, `quickstart.md`

**Tests**: Bắt buộc theo `DUT AI Manager Constitution v1.14.0` (Quality Gate #1 & #4: mọi thay đổi Domain Entity, Use Case và tính toán trọng yếu phải có unit/integration tests `pytest`, Frontend phải pass `npm run build`).

**Organization**: Các tác vụ được nhóm theo từng User Story (`US1` → `US5`) để mỗi story có thể triển khai, kiểm thử và bàn giao độc lập theo thứ tự ưu tiên.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Có thể chạy song song (khác file, không phụ thuộc vào tác vụ chưa xong)
- **[Story]**: Nhãn User Story tương ứng (`[US1]`, `[US2]`, `[US3]`, `[US4]`, `[US5]`) — chỉ áp dụng cho Phase 3 đến Phase 7
- Mỗi tác vụ ghi rõ đường dẫn file tuyệt đối theo gốc repository (`backend/...`, `frontend/...`) và trích dẫn rõ ràng ràng buộc dữ liệu từ `data-model.md` và `contracts/api-contracts.md`.

---

## Phase 1: Setup (Database Migration & Baseline)

**Purpose**: Kiểm chứng trạng thái nền và chuẩn bị migration lược đồ cơ sở dữ liệu dùng chung cho toàn bộ tính năng.

- [X] T001 Chạy kiểm tra baseline test suite hiện tại tại `backend/tests/unit/homework/` và kiểm tra trạng thái Alembic head (`b0a90fa04270`) trước khi thay đổi mã nguồn
- [X] T002 Tạo Alembic migration `backend/alembic/versions/044_hw_exercises_and_sub_id.py` với `revision = "044_hw_exercises_and_sub_id"` (≤ 32 ký tự) và `down_revision = "b0a90fa04270"`: tạo bảng `homework_exercises` (`id` INTEGER PK autoincrement, `homework_id` INTEGER FK `homeworks.id` ON DELETE CASCADE NOT NULL, `exercise_id` VARCHAR(64) NOT NULL, `title` VARCHAR(255) NOT NULL, `order_index` INTEGER NOT NULL default `0`, `is_active` BOOLEAN NOT NULL default `true`, `created_at` TIMESTAMPTZ NOT NULL, `updated_at` TIMESTAMPTZ NOT NULL, `UNIQUE (homework_id, exercise_id)` tên `uq_hw_exercises_hw_ex`, `INDEX ix_hw_exercises_hw_active (homework_id, is_active)`); thêm cột `homeworks.last_synced_at` TIMESTAMPTZ NULL; thêm cột `homework_submissions.external_submission_id` VARCHAR(128) NULL; chạy SQL backfill `external_submission_id` từ `details->>'submission_id'` / `details->>'session_id'`, khử bản ghi trùng ưu tiên `is_passed = TRUE` rồi `submitted_at` sớm nhất, tạo PostgreSQL partial unique index `uq_hw_sub_external_id` trên `(homework_id, user_id, submission_type, external_submission_id) WHERE external_submission_id IS NOT NULL`, và cài đặt đầy đủ `downgrade()`

---

## Phase 2: Foundational (Core Domain SSOT, ORM, Repositories & In-Memory Fakes)

**Purpose**: Xây dựng lõi Domain 2 chiều, bảng `homework_exercises`, cơ chế lưu vết append-only và toàn bộ Repository Ports/Implementations làm nền tảng bắt buộc trước khi triển khai các User Story.

**⚠️ CRITICAL**: Không bắt đầu bất kỳ User Story nào cho tới khi Phase 2 hoàn tất và unit test thuần domain đạt 100% pass.

- [X] T003 [P] Định nghĩa `CompletionStatus` (`StrEnum`: `NOT_STARTED`, `IN_PROGRESS`, `COMPLETED`), `TimelinessStatus` (`StrEnum`: `ON_TIME`, `LATE`, `UPCOMING`, `OVERDUE`), `ExerciseEvaluation` (`BaseModel` `frozen=True` gồm `exercise_id: str`, `title: str`, `order_index: int`, `is_submitted: bool`, `is_passed: bool`, `first_passed_at: datetime | None`, `latest_submitted_at: datetime | None`, `best_score: float | None`, `attempt_count: int`, `is_late: bool`) và nâng cấp `SubmissionEvaluation` (`completion_status`, `timeliness_status`, `is_submitted`, `is_completed_on_time`, `is_late`, `is_overdue`, `completed_at`, `coding_submitted`, `coding_is_late`, `coding_status`, `total_coding_required`, `total_coding_completed`, `coding_exercises`, `game_submitted`, `game_is_late`, `game_first_passed_at`, `game_best_score`, `uncompleted_items`) trong `backend/app/homework/domain/value_objects.py`
- [X] T004 Cập nhật `backend/app/homework/domain/entity.py`: thêm entity `HomeworkExercise(BaseGenericEntity[int])` (`homework_id: int`, `exercise_id: str`, `title: str`, `order_index: int = 0`, `is_active: bool = True`), thêm `Homework.last_synced_at: datetime | None = None`, thêm `HomeworkSubmission.external_submission_id: str | None = None` (cập nhật `create_coding` và `create_game`), và viết lại `Homework.evaluate_submissions(submissions, required_exercises, deadline=None, reference_time=None)` làm SSOT 2 chiều duy nhất (chỉ xét `is_active == True`, KHÔNG loại bài nộp trễ khỏi trạng thái hoàn thành, dùng `min(ensure_utc(s.submitted_at))` của các lượt `is_passed == True` làm `first_passed_at`, xử lý legacy `requires_coding=False & requires_game=False` thành `has_coding=True`)
- [X] T005 [P] Tạo `HomeworkExerciseRepositoryPort` trong `backend/app/homework/domain/ports/homework_exercise_repository_port.py` với các method trừu tượng `get_active_by_homework(homework_id: int) -> list[HomeworkExercise]`, `get_active_by_homework_ids(homework_ids: list[int]) -> dict[int, list[HomeworkExercise]]`, `sync_exercises(homework_id: int, exercises: list[HomeworkExercise]) -> list[HomeworkExercise]` và export qua `backend/app/homework/domain/ports/__init__.py`
- [X] T006 [P] Cập nhật `HomeworkSubmissionRepositoryPort` trong `backend/app/homework/domain/ports/homework_submission_repository_port.py`: xóa bỏ `get_required_exercise_ids_map()`, cập nhật chữ ký `find_submission_match(...)` ưu tiên tham số `external_submission_id: str | None = None` (cấm match chỉ bằng `exercise_id`), và chuẩn hóa kiểu trả về của `get_user_submissions_for_homeworks()` thành `list[HomeworkSubmission]`
- [X] T007 Cập nhật SQLAlchemy ORM models trong `backend/app/homework/infrastructure/model.py`: thêm `HomeworkExerciseModel` (khớp đúng schema `homework_exercises` với `UniqueConstraint("homework_id", "exercise_id", name="uq_hw_exercises_hw_ex")` và `Index("ix_hw_exercises_hw_active", "homework_id", "is_active")`, cài đặt `to_entity()`/`from_entity()`), thêm `HomeworkModel.last_synced_at` (`DateTime(timezone=True)`, nullable) và quan hệ `exercises`, thêm `HomeworkSubmissionModel.external_submission_id` (`String(128)`, nullable, index) kèm `to_entity()`/`from_entity()`
- [X] T008 [P] Triển khai `HomeworkExerciseRepository(HomeworkExerciseRepositoryPort)` trong `backend/app/homework/infrastructure/homework_exercise_repository.py` (sắp xếp theo `order_index ASC, exercise_id ASC`; `sync_exercises` thực hiện upsert theo `(homework_id, exercise_id)` với `is_active=True` và đặt `is_active=False` cho các bài con không còn trong danh sách mới)
- [X] T009 [P] Cập nhật `HomeworkRepository` trong `backend/app/homework/infrastructure/homework_repository.py`: lưu/cập nhật `last_synced_at` trong `create`/`update`, và bổ sung method hỗ trợ truy vấn danh sách bài tập được giao kèm lọc `search` không phân biệt hoa thường trên `HomeworkModel.title`
- [X] T010 [P] Cập nhật `HomeworkSubmissionRepository` trong `backend/app/homework/infrastructure/homework_submission_repository.py`: xóa hoàn toàn `get_required_exercise_ids_map()`; viết lại `find_submission_match()` xóa nhánh match Coding chỉ theo `(homework_id, user_id, exercise_id)`, chỉ match theo `(homework_id, user_id, submission_type, external_submission_id)` khi có `external_submission_id` hoặc fallback khớp chính xác `(homework_id, user_id, submission_type, exercise_id, submitted_at)` khi thiếu ID; cập nhật `update_submission()` hỗ trợ `external_submission_id`
- [X] T011 [P] Tạo `InMemoryHomeworkExerciseRepository` trong `backend/app/homework/infrastructure/in_memory/in_memory_exercise_repo.py`, cập nhật `backend/app/homework/infrastructure/in_memory/in_memory_submission_repo.py` đồng bộ hành vi append-only + xóa `get_required_exercise_ids_map()`, và export trong `backend/app/homework/infrastructure/in_memory/__init__.py`
- [X] T012 Cập nhật test fixtures trong `backend/tests/fixtures/homework_fixtures.py` (factory tạo `HomeworkExercise` & multi-attempt `HomeworkSubmission` có `external_submission_id`) và viết/cập nhật unit tests trong `backend/tests/unit/homework/test_homework_pure_domain.py` và `backend/tests/unit/homework/test_homework_ports_contract.py` bao phủ đầy đủ ma trận 2 chiều (`ON_TIME`, `LATE`, `UPCOMING`, `OVERDUE`), nộp lại sau hạn giữ nguyên `ON_TIME`, nộp trượt sau khi đã đạt, bài con `is_active=False` và bản ghi di sản `legacy-...`/`sync-...`

**Checkpoint**: Nền tảng Domain SSOT + ORM + Repositories + InMemory Fakes sẵn sàng và pass 100% pure domain tests (`uv run pytest tests/unit/homework/test_homework_pure_domain.py tests/unit/homework/test_homework_ports_contract.py`).

---

## Phase 3: User Story 1 - Hiển Thị Chính Xác Trạng Thái Hoàn Thành Bài Tập Trên Trang Bài Tập Của Tôi (Priority: P1) 🎯 MVP

**Goal**: Học viên truy cập `/dashboard/my-homeworks` thấy chính xác 100% trạng thái từng thẻ bài tập ("Đã hoàn thành • Đúng hạn", "Đã hoàn thành • Nộp trễ", "Đang làm dở", "Quá hạn nộp", "Chưa nộp bài") lấy trực tiếp từ SSOT Backend mà không bị báo sai "Chưa nộp / Chưa làm đủ".

**Independent Test**: Giao cho học viên các bài tập với đủ tổ hợp (Coding nhiều bài con, Game, cả hai) ở các trạng thái đúng hạn, nộp trễ, làm dở, chưa làm, nộp lại sau hạn; kiểm tra `GET /api/v1/homeworks/me` và giao diện `/dashboard/my-homeworks` hiển thị khớp 100% thực tế.

### Tests for User Story 1

- [X] T013 [P] [US1] Cập nhật unit tests `backend/tests/unit/homework/test_get_user_homeworks.py` kiểm chứng `GetUserHomeworksUseCase` trả đúng `completion_status`, `timeliness_status`, `is_submitted`, `is_late`, `is_overdue`, `total_coding_required/completed`, `MyHomeworksStats` cho các kịch bản: hoàn thành đúng hạn, hoàn thành trễ hạn (`COMPLETED + LATE`), nộp lại sau hạn vẫn `ON_TIME`, làm dở và chưa nộp

### Implementation for User Story 1

- [X] T014 [P] [US1] Mở rộng `HomeworkResponse` trong `backend/app/homework/application/dtos/homework_dtos.py` (thêm `last_synced_at: datetime | None = None`, `completion_status: CompletionStatus = CompletionStatus.NOT_STARTED`, `timeliness_status: TimelinessStatus = TimelinessStatus.UPCOMING`, `completed_at: datetime | None = None`, `is_late: bool = False`, `coding_is_late: bool = False`, `game_is_late: bool = False`, helper `from_evaluation(...)`), thêm `MyHomeworksStats` (`total`, `completed`, `completed_on_time`, `completed_late`, `uncompleted`, `overdue`) và `MyHomeworksPageResponse` (`items: list[HomeworkResponse]`, `stats: MyHomeworksStats`), export trong `backend/app/homework/application/dtos/__init__.py`
- [X] T015 [US1] Viết lại `GetUserHomeworksUseCase` trong `backend/app/homework/application/get_user_homeworks_use_case.py` inject bắt buộc `HomeworkExerciseRepositoryPort` (non-nullable theo Nguyên tắc XIV), đánh giá 100% bài được giao qua `Homework.evaluate_submissions()` để tính `MyHomeworksStats` tổng chính xác, sau đó lọc theo `status` (`all | uncompleted | completed | overdue`), `search` (không phân biệt hoa/thường theo `title`) và phân trang (`page`, `page_size`)
- [X] T016 [US1] Đăng ký `HomeworkExerciseRepository` / `HomeworkExerciseRepositoryPort` và cập nhật `get_get_user_homeworks_use_case` trong `backend/app/homework/providers.py`; nâng cấp endpoint `GET /api/v1/homeworks/me` trong `backend/app/homework/controller.py` nhận query params `status: Literal["all", "uncompleted", "completed", "overdue"] = "all"` và `search: str | None = None`, trả về `ApiResponse[MyHomeworksPageResponse]` kèm `pagination`
- [X] T017 [US1] Chạy `npm run generate:api` cập nhật `frontend/src/types/api.generated.d.ts`, cập nhật type aliases từ OpenAPI `Schema<...>` trong `frontend/src/features/homework/types/homework.types.ts`, cập nhật `homeworkService.getMyHomeworks({ page, pageSize, status, search })` trong `frontend/src/features/homework/services/homework.service.ts` và hook `useMyHomeworks(...)` trong `frontend/src/features/homework/hooks/useHomeworks.ts`
- [X] T018 [US1] Viết lại `frontend/src/features/homework/components/HomeworkCard.tsx` thành component trình bày thuần túy theo `homework.completion_status` và `homework.timeliness_status` (xóa sạch logic tự tính `isSubmitted`/`isOverdue`/`isCodingPartial`/`isBothPartial`/`isPartial`; hiển thị badge xanh lá "Đã hoàn thành • Đúng hạn", badge xanh ngọc/amber "Đã hoàn thành • Nộp trễ", "Đang làm dở", "Quá hạn (Làm dở)", "Chưa nộp bài", "Quá hạn nộp"; hiển thị thời gian `last_synced_at` nếu có)
- [X] T019 [US1] Cập nhật `frontend/src/features/homework/pages/MyHomeworkPage.tsx`: xóa bỏ lời gọi `useUnsubmittedByUser` và xóa toàn bộ logic tự tính `processedHomeworks` / `filteredHomeworks` / `stats` phía client, đọc trực tiếp `items` và `stats` từ `useMyHomeworks`

**Checkpoint**: User Story 1 (MVP) hoàn tất — Trang `/dashboard/my-homeworks` hiển thị chính xác trạng thái hoàn thành 2 chiều và không còn báo sai "Chưa nộp / Chưa làm đủ".

---

## Phase 4: User Story 2 - Đồng Nhất 100% Trạng Thái Giữa Trang Chủ, Bài Tập Của Tôi, Chi Tiết Bài Tập Và Báo Cáo Quản Trị (Priority: P1)

**Goal**: Toàn bộ 4 màn hình (Trang chủ, Bài tập của tôi, Chi tiết bài tập của tôi, Quản trị & Báo cáo chưa nộp) cùng đọc danh mục bài con từ `homework_exercises` và đánh giá qua duy nhất `Homework.evaluate_submissions()`, đảm bảo 0% sai lệch và hiển thị đúng hạn nộp cá nhân ở trang chi tiết học viên.

**Independent Test**: Kiểm tra cùng một học viên trên cả 4 góc nhìn (Trang chủ `unsubmitted_homeworks`, `/dashboard/my-homeworks`, `/dashboard/my-homeworks/:id`, và màn hình quản trị `submission-status`) cho cùng tập bài tập (bao gồm học viên có hạn nộp cá nhân được gia hạn); xác minh trạng thái, số bài con `X/Y`, và hạn nộp cá nhân khớp 100%.

### Tests for User Story 2

- [X] T020 [P] [US2] Tạo unit test `backend/tests/unit/homework/test_get_my_homework_detail.py` kiểm chứng `GetMyHomeworkDetailUseCase` trả đúng deadline cá nhân (kể cả khi khác `min(deadlines)` lớp), trả đủ `coding_exercises` kèm trạng thái từng bài con, lịch sử `submissions`, và trả `None`/404 khi user không phải assignee
- [X] T021 [P] [US2] Cập nhật `backend/tests/unit/homework/test_homework_ssot.py` và `backend/tests/unit/homework/test_get_homework_detail_use_case.py` kiểm chứng đồng nhất 100% trạng thái & tiến độ giữa `GetUserHomeworksUseCase`, `GetMyHomeworkDetailUseCase`, `GetUnsubmittedHomeworksForUserUseCase`, `GetUnsubmittedHomeworkReportUseCase` và `GetHomeworkSubmissionStatusUseCase`

### Implementation for User Story 2

- [X] T022 [P] [US2] Thêm `MyHomeworkExerciseStatusDTO` (`exercise_id`, `title`, `order_index`, `is_submitted`, `is_passed`, `first_passed_at`, `latest_submitted_at`, `best_score`, `attempt_count`, `is_late`) trong `backend/app/homework/application/dtos/submission_dtos.py` và `MyHomeworkDetailResponse` (`homework: HomeworkResponse`, `coding_exercises: list[MyHomeworkExerciseStatusDTO]`, `submissions: list[HomeworkSubmissionDetailResponse]`) trong `backend/app/homework/application/dtos/homework_dtos.py`, export trong `backend/app/homework/application/dtos/__init__.py`
- [X] T023 [P] [US2] Triển khai `GetMyHomeworkDetailUseCase` trong `backend/app/homework/application/get_my_homework_detail_use_case.py` (1 public `execute(homework_id: int, user_id: int) -> MyHomeworkDetailResponse | None`, kiểm tra học viên thuộc `homework_assignees` và lấy deadline cá nhân, nạp `active_exercises` từ `HomeworkExerciseRepositoryPort`, nạp `submissions` từ `HomeworkSubmissionRepositoryPort`, đánh giá qua `Homework.evaluate_submissions()`)
- [X] T024 [P] [US2] Cập nhật `GetUnsubmittedHomeworksForUserUseCase` trong `backend/app/homework/application/get_unsubmitted_homeworks_for_user_use_case.py` và `GetUnsubmittedHomeworkReportUseCase` trong `backend/app/homework/application/get_unsubmitted_homework_report_use_case.py`: thay `get_required_exercise_ids_map()` bằng `HomeworkExerciseRepositoryPort.get_active_by_homework_ids()`, nạp deadline cá nhân đầy đủ, và chỉ xem là chưa nộp khi `eval_result.completion_status != CompletionStatus.COMPLETED`
- [X] T025 [P] [US2] Cập nhật `GetHomeworkDetailUseCase` trong `backend/app/homework/application/get_homework_detail_use_case.py` đọc `coding_exercises` từ `HomeworkExerciseRepositoryPort`; refactor `GetHomeworkSubmissionStatusUseCase` trong `backend/app/homework/application/get_homework_submission_status_use_case.py` xóa bỏ logic tính tay `_evaluate_student`, gọi thẳng `homework.evaluate_submissions(user_subs, required_exercises=active_exercises, deadline=assignee.deadline, reference_time=now)` cho từng assignee và ánh xạ sang `StudentHomeworkDetailDTO` / `UserSubmissionInfo`
- [X] T026 [US2] Đăng ký `GetMyHomeworkDetailUseCase` và cập nhật toàn bộ provider read use cases trong `backend/app/homework/providers.py`, export trong `backend/app/homework/application/__init__.py`, và thêm endpoint `GET /api/v1/homeworks/me/{homework_id}` (`ApiResponse[MyHomeworkDetailResponse]`, trả 404 nếu `None`) trong `backend/app/homework/controller.py`
- [X] T027 [P] [US2] Chạy `npm run generate:api` đồng bộ types cho `MyHomeworkDetailResponse`, bổ sung `homeworkService.getMyHomeworkDetail(id)` trong `frontend/src/features/homework/services/homework.service.ts` và hook `useMyHomeworkDetail(id)` trong `frontend/src/features/homework/hooks/useHomeworks.ts`; tạo subcomponent `frontend/src/features/homework/components/MyHomeworkExerciseChecklist.tsx` hiển thị trạng thái từng bài tập con bắt buộc từ Backend và export qua `frontend/src/features/homework/components/index.ts`
- [X] T028 [US2] Refactor `frontend/src/features/homework/pages/MyHomeworkDetailPage.tsx` chuyển sang gọi `useMyHomeworkDetail(homeworkId)`, xóa toàn bộ logic tự tính `isCodingCompleted`/`isGamePassed`/`isFullyPassed`/`isOverdue` trên client, hiển thị đúng hạn nộp cá nhân của học viên, badge trạng thái 2 chiều từ `homework.completion_status`/`homework.timeliness_status` và `MyHomeworkExerciseChecklist`
- [X] T029 [P] [US2] Cập nhật `frontend/src/pages/HomePage.tsx` hiển thị nhãn đúng theo `completion_status` và `timeliness_status` (`Quá hạn` / `Đang làm dở` / `Chưa nộp`) cho danh sách `unsubmitted_homeworks` và thêm điều hướng khi click vào từng mục sang `/dashboard/my-homeworks/${hw.id}`

**Checkpoint**: Cả 4 màn hình (Trang chủ, Bài tập của tôi, Chi tiết bài tập cá nhân, Quản trị) đồng nhất 100% cùng một SSOT.

---

## Phase 5: User Story 3 - Danh Mục Yêu Cầu Bài Tập Chính Thức Và Miễn Nhiễm Với Dữ Liệu Lỗi Hoặc Di Sản (Priority: P2)

**Goal**: Thiết lập và duy trì danh mục `homework_exercises` chính thức xuyên suốt vòng đời bài tập (tạo, sửa, đồng bộ, backfill dữ liệu cũ), gỡ bỏ vĩnh viễn `HomeworkExerciseResolver` và chấm dứt mọi ảnh hưởng từ bản ghi nộp bài lỗi/di sản hoặc bài con đã bị xóa.

**Independent Test**: Tạo/sửa/đồng bộ một bài tập có 2 bài con chính thức, thêm bản ghi nộp lỗi `legacy-...`/`sync-...` và gỡ 1 bài con rồi sync lại; xác minh `homework_exercises` cập nhật `is_active` chính xác, `SyncHomeworkFromQuizUseCase` tôn trọng `is_passed=False` từ Quiz API, và học viên làm đủ bài con active đạt `COMPLETED`.

### Tests for User Story 3

- [X] T030 [P] [US3] Cập nhật `backend/tests/integration/homework/test_homework_quiz_integration.py` và `backend/tests/unit/homework/test_homework_in_memory_use_cases.py` kiểm chứng: (1) tạo/sửa/đồng bộ lưu đúng `homework_exercises` và `last_synced_at`, (2) khi Quiz gỡ bài con thì đặt `is_active=False` và khi Quiz lỗi mạng thì giữ nguyên danh mục hiện có (fail-safe), (3) sync Coding tôn trọng `is_passed`/`status` thực tế từ Quiz API, (4) bản ghi di sản không làm tăng `total_coding_required`

### Implementation for User Story 3

- [X] T031 [P] [US3] Cập nhật `CreateHomeworkUseCase` trong `backend/app/homework/application/create_homework_use_case.py` và `UpdateHomeworkUseCase` trong `backend/app/homework/application/update_homework_use_case.py`: khi `requires_coding=True`, gọi `quiz_api.get_lesson_exercises(extracted_slug)` và lưu danh mục bài con qua `HomeworkExerciseRepositoryPort.sync_exercises(...)`, đồng thời cập nhật `homework.last_synced_at = datetime.now(UTC)`
- [X] T032 [US3] Cập nhật `SyncHomeworkFromQuizUseCase` trong `backend/app/homework/application/sync_homework_use_case.py` và `SyncHomeworkResult` (`last_synced_at: datetime | None = None`) trong `backend/app/homework/application/dtos/homework_dtos.py`: đồng bộ danh mục `homework_exercises` fail-safe (chỉ `sync_exercises` khi `get_lesson_exercises` trả về danh sách hợp lệ), tôn trọng trạng thái đạt/không đạt thực tế (`is_passed` hoặc `status in ("PASSED", "ACCEPTED", "COMPLETED")`) cho Coding thay vì ép cứng `is_passed=True`, lưu `external_submission_id` (`submission_id` cho Coding, `session_id` cho Game), và cập nhật `homeworks.last_synced_at = datetime.now(UTC)`
- [X] T033 [US3] Thêm `BackfillHomeworkExercisesResult` (`total_homeworks`, `succeeded`, `skipped_no_slug`, `failed`, `failed_details`) trong `backend/app/homework/application/dtos/homework_dtos.py`, triển khai `BackfillHomeworkExercisesUseCase` trong `backend/app/homework/application/backfill_homework_exercises_use_case.py`, tạo CLI script `backend/app/scripts/backfill_homework_exercises.py`, đăng ký provider trong `backend/app/homework/providers.py` và gắn admin endpoint `POST /api/v1/homeworks/admin/backfill-exercises` (`HomeworkPermission.CREATE`) trong `backend/app/homework/controller.py`
- [X] T034 [US3] Xóa file `backend/app/homework/application/homework_exercise_resolver.py`, gỡ toàn bộ import/export khỏi `backend/app/homework/application/__init__.py` và `backend/app/homework/providers.py`, và cập nhật `RescanAllHomeworksUseCase` trong `backend/app/homework/application/rescan_all_homeworks_use_case.py` dùng `HomeworkExerciseRepositoryPort` thay vì `HomeworkExerciseResolver` (đồng thời sửa lỗi thiếu `self.quiz_api` nếu có)

**Checkpoint**: Danh mục bài tập con chính thức được quản lý khép kín ở mọi thao tác ghi/đồng bộ/backfill; `HomeworkExerciseResolver` và `get_required_exercise_ids_map` đã bị loại bỏ hoàn toàn.

---

## Phase 6: User Story 4 - Lọc, Tìm Kiếm, Phân Trang Đầy Đủ Và Đồng Bộ Minh Bạch Trên Trang Bài Tập Của Tôi (Priority: P2)

**Goal**: Học viên có trên 20 bài tập xem đủ thống kê tổng quan, lọc trạng thái, tìm kiếm tên bài tập và phân trang chính xác phía máy chủ, đồng thời có thể chủ động bấm đồng bộ nhanh các bài chưa hoàn thành từ hệ thống Quiz.

**Independent Test**: Tạo 30 bài tập với đủ trạng thái cho một học viên; xác minh trang 1/trang 2 phân trang chuẩn, 4 thẻ thống kê luôn giữ tổng 30 khi lọc hoặc chuyển trang, tìm kiếm tìm ra bài ở vị trí thứ 25, và nút "Đồng bộ từ Quiz" cập nhật tức thời cả trang Bài tập của tôi lẫn Trang chủ.

### Tests for User Story 4

- [X] T035 [P] [US4] Mở rộng `backend/tests/unit/homework/test_get_user_homeworks.py` và `backend/tests/api/homework/test_homework_api.py` kiểm chứng: phân trang 30 bài (`page=1` có 20 bài, `page=2` có 10 bài, `stats.total == 30` ở cả 2 trang), lọc `status=uncompleted|completed|overdue`, tìm kiếm `search` không phân biệt hoa thường trên bài ở trang 2, và kiểm thử `SyncMyUnsubmittedHomeworksUseCase` / `POST /api/v1/homeworks/me/sync` (giới hạn tối đa 10 bài, fail-safe khi 1 bài lỗi)

### Implementation for User Story 4

- [X] T036 [P] [US4] Thêm `SyncMyHomeworksResult` (`total_checked`, `synced_count`, `failed_count`, `results: list[SyncHomeworkResult]`, `failed_homework_ids: list[int]`) trong `backend/app/homework/application/dtos/homework_dtos.py`, triển khai `SyncMyUnsubmittedHomeworksUseCase` trong `backend/app/homework/application/sync_my_unsubmitted_homeworks_use_case.py` (chỉ chọn tối đa 10 bài chưa `COMPLETED` có slug của `current_user`, chạy tuần tự fail-safe qua `SyncHomeworkFromQuizUseCase`), đăng ký provider trong `backend/app/homework/providers.py`, export trong `backend/app/homework/application/__init__.py`, và gắn endpoint `POST /api/v1/homeworks/me/sync` trong `backend/app/homework/controller.py`
- [X] T037 [P] [US4] Chạy `npm run generate:api`, bổ sung `homeworkService.syncMyUnsubmitted()` trong `frontend/src/features/homework/services/homework.service.ts` và hook `useSyncMyUnsubmitted()` trong `frontend/src/features/homework/hooks/useHomeworks.ts` (khi thành công invalidate cả `['homeworks']` và `['dashboard']` — đồng thời bổ sung invalidate `['dashboard']` cho `useSyncHomeworkFromQuiz()`)
- [X] T038 [P] [US4] Tách subcomponent `frontend/src/features/homework/components/MyHomeworkStatsCards.tsx` (hiển thị 4 thẻ thống kê `Tất cả`, `Đã hoàn thành` kèm chú thích Đúng hạn/Nộp trễ, `Chưa hoàn thành`, `Quá hạn`) và `frontend/src/features/homework/components/MyHomeworkFilterBar.tsx` (tabs `Tất cả` / `Chưa hoàn thành` / `Đã hoàn thành` / `Quá hạn` + ô tìm kiếm debounce 300ms) và export qua `frontend/src/features/homework/components/index.ts`
- [X] T039 [US4] Hoàn thiện `frontend/src/features/homework/pages/MyHomeworkPage.tsx` làm orchestrator thuần theo Nguyên tắc VIII & XII: tích hợp `MyHomeworkStatsCards`, `MyHomeworkFilterBar`, nút **"Đồng bộ từ Quiz"** gọi `useSyncMyUnsubmitted()`, thanh Ant Design `Pagination` (`defaultPageSize: 20`, `pageSizeOptions: ['10', '20', '50', '100']`, `showSizeChanger: true`, `showTotal`), và reset `page = 1` ngay khi thay đổi `activeTab` hoặc `searchText`

**Checkpoint**: Trang "Bài tập của tôi" hỗ trợ đầy đủ thống kê tổng, lọc/tìm kiếm/phân trang phía server và đồng bộ nhanh minh bạch.

---

## Phase 7: User Story 5 - Bảo Toàn Lịch Sử Nộp Bài Và Quy Tắc Xét Vi Phạm Kỷ Luật Công Bằng (Priority: P3)

**Goal**: Webhook nộp bài ghi nhận lịch sử append-only không ghi đè mốc nộp trước hạn, và job kiểm tra vi phạm quá hạn phân biệt công bằng giữa học viên đã hoàn thành đúng hạn (dù nộp lại sau hạn) với học viên nộp trễ hoặc chưa hoàn thành.

**Independent Test**: Mô phỏng webhook gửi lần nộp đạt trước hạn rồi gửi tiếp lần nộp thứ 2 sau hạn (đạt hoặc trượt) với `submission_id` khác nhau; xác minh cả 2 bản ghi được bảo toàn, gửi lặp cùng `submission_id` không tạo bản ghi trùng, và `CheckOverdueHomeworkUseCase` không tạo vi phạm cho học viên nộp đúng hạn trong khi vẫn phát hiện vi phạm nộp trễ cho học viên hoàn thành sau hạn.

### Tests for User Story 5

- [X] T040 [P] [US5] Cập nhật `backend/tests/integration/homework/test_homework_webhook.py` và `backend/tests/unit/homework/test_homework_checker.py` kiểm chứng: (1) webhook lưu 2 lượt nộp riêng biệt cho 2 `submission_id` khác nhau của cùng `exercise_id` không ghi đè `submitted_at`, (2) gửi lặp cùng `submission_id` thực hiện idempotent update không tạo trùng, (3) `CheckOverdueHomeworkUseCase` không phạt học viên nộp đạt đúng hạn rồi nộp lại sau hạn, và phát sự kiện vi phạm với lý do plain-text `"Nộp bài tập trễ hạn (...)"` cho học viên `COMPLETED + LATE`

### Implementation for User Story 5

- [X] T041 [US5] Cập nhật `RecordHomeworkSubmissionUseCase` trong `backend/app/homework/application/record_submission_use_case.py` trích xuất và lưu `external_submission_id` (từ `payload.submission_id` hoặc `details.submission_id` cho Coding; `details.session_id` hoặc `payload.submission_id` cho Game), gọi `find_submission_match(..., external_submission_id=...)` để ghi mới theo chế độ append-only cho mỗi lượt nộp mới và chỉ idempotent update khi trùng chính xác lượt nộp đó
- [X] T042 [US5] Cập nhật `CheckOverdueHomeworkUseCase` trong `backend/app/homework/application/check_overdue_homework_use_case.py` dùng `HomeworkExerciseRepositoryPort` + `Homework.evaluate_submissions()`, bỏ kiểm tra thủ công, chỉ phát `HomeworkOverdueDetected` khi `not eval_result.is_completed_on_time`, và tạo thông điệp plain-text sạch (Nguyên tắc XI): `"Nộp bài tập trễ hạn ({title})"` khi `completion_status == COMPLETED` và `"Chưa hoàn thành {items} ({title})"` khi chưa hoàn thành

**Checkpoint**: Toàn bộ 5 User Stories hoàn chỉnh, lịch sử nộp bài bất biến và cơ chế kiểm tra vi phạm kỷ luật hoạt động công bằng, nhất quán.

---

## Phase 8: Polish & Cross-Cutting Verification

**Purpose**: Kiểm tra chất lượng toàn diện, dọn dẹp mã chết, kiểm chứng kiểu tĩnh, build và diễn tập quy trình `quickstart.md`.

- [X] T043 [P] Rà soát toàn bộ repository đảm bảo không còn tham chiếu chết tới `get_required_exercise_ids_map`, `HomeworkExerciseResolver`, hoặc `useUnsubmittedByUser` trong `MyHomeworkPage`, và chạy `uv run ruff check app/homework tests/unit/homework tests/integration/homework tests/api/homework` đạt 0 lỗi (bao gồm rule `DTZ`)
- [X] T044 Chạy toàn bộ backend test suite `uv run pytest tests/unit/homework tests/integration/homework tests/api/homework -v` đảm bảo 100% pass và không gây hồi quy cho các test hiện hữu
- [X] T045 Chạy kiểm tra cuối cùng tại `frontend/`: `npm run generate:api`, `npm run lint`, và `npm run build` (`tsc -b && vite build`) đảm bảo 0 lỗi TypeScript/ESLint/bundle
- [X] T046 Kiểm chứng Alembic migration `uv run alembic upgrade head` và thử nghiệm kịch bản xác thực đầu-cuối theo `specs/073-rebuild-homework-tracking/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Bắt đầu ngay lập tức (`T001` → `T002`).
- **Phase 2 (Foundational)**: Phụ thuộc Phase 1 (`T002`) — **CHẶN toàn bộ User Stories** cho tới khi hoàn tất `T012`.
- **Phase 3 (US1 - P1 🎯 MVP)**: Phụ thuộc Phase 2 (`T012`). Độc lập hoàn toàn với các story khác.
- **Phase 4 (US2 - P1)**: Phụ thuộc Phase 2 (`T012`) và dùng `HomeworkResponse` đã mở rộng ở `T014` (US1).
- **Phase 5 (US3 - P2)**: Phụ thuộc Phase 2 (`T012`). Tác vụ xóa `HomeworkExerciseResolver` (`T034`) thực hiện sau khi US2 (`T025`) và US5 (`T042`) đã gỡ phụ thuộc khỏi resolver.
- **Phase 6 (US4 - P2)**: Phụ thuộc US1 (`T015`, `T016`, `T019`) và US3 (`T032` để `SyncMyUnsubmittedHomeworksUseCase` gọi `SyncHomeworkFromQuizUseCase` bản mới).
- **Phase 7 (US5 - P3)**: Phụ thuộc Phase 2 (`T012`). Độc lập với US1/US4 về mã nguồn, nên hoàn thành trước `T034` để gỡ sạch `HomeworkExerciseResolver`.
- **Phase 8 (Polish)**: Phụ thuộc hoàn tất toàn bộ các Phase cần bàn giao.

### Parallel Opportunities

- **Trong Phase 2**: `T003`, `T005`, `T006` chạy song song → sau `T004` & `T007`, các repo `T008`, `T009`, `T010`, `T011` chạy song song.
- **Trong Phase 3 (US1)**: `T013` và `T014` chạy song song; sau `T017`, có thể hoàn thiện `T018` trước hoặc song song với kiểm thử backend.
- **Trong Phase 4 (US2)**: `T020`, `T021`, `T022`, `T023`, `T024`, `T025` đều khác file nên có thể triển khai song song hoàn toàn; phía Frontend `T027` và `T029` chạy song song.
- **Trong Phase 5 (US3)**: `T030` và `T031` chạy song song.
- **Trong Phase 6 (US4)**: Backend `T036` và Frontend subcomponents `T038` có thể thực hiện song song.
- **Trong Phase 7 (US5)**: `T040` chạy song song khi bắt đầu; `T041` và `T042` đụng 2 file độc lập nên có thể thực hiện song song.

---

## Parallel Example: User Story 2

```bash
# Nhóm tác vụ Backend độc lập file trong US2 có thể chạy song song:
Task T022: "Thêm MyHomeworkExerciseStatusDTO & MyHomeworkDetailResponse trong backend/app/homework/application/dtos/"
Task T023: "Triển khai GetMyHomeworkDetailUseCase trong backend/app/homework/application/get_my_homework_detail_use_case.py"
Task T024: "Cập nhật GetUnsubmittedHomeworksForUserUseCase & GetUnsubmittedHomeworkReportUseCase"
Task T025: "Cập nhật GetHomeworkDetailUseCase & refactor GetHomeworkSubmissionStatusUseCase dùng SSOT"

# Nhóm tác vụ Frontend độc lập file trong US2 có thể chạy song song sau khi sinh OpenAPI types:
Task T027: "Tạo MyHomeworkExerciseChecklist.tsx & hook useMyHomeworkDetail"
Task T029: "Cập nhật HomePage.tsx hiển thị đúng nhãn trạng thái & điều hướng chi tiết"
```

---

## Implementation Strategy

### MVP First (User Story 1 + User Story 2 — Cả 2 cùng Priority P1)

1. Hoàn tất **Phase 1 (Setup)** + **Phase 2 (Foundational)** → khóa chặt Domain SSOT 2 chiều và lược đồ `homework_exercises` + `external_submission_id`.
2. Hoàn tất **Phase 3 (US1)** → dừng kiểm chứng ngay trang `/dashboard/my-homeworks` hết sạch bug báo sai "Chưa nộp / Chưa làm đủ".
3. Hoàn tất **Phase 4 (US2)** → đồng nhất Trang chủ (`/dashboard`), Chi tiết bài tập cá nhân (`/dashboard/my-homeworks/:id`) và màn hình Quản trị.
4. Tiếp tục **Phase 5 (US3)** + **Phase 7 (US5)** → kích hoạt đồng bộ danh mục bài con tự động, webhook append-only, kiểm tra vi phạm công bằng và chạy backfill dữ liệu cũ.
5. Hoàn tất **Phase 6 (US4)** + **Phase 8 (Polish)** → hoàn thiện phân trang/lọc/tìm kiếm server-driven, nút đồng bộ nhanh và kiểm tra chất lượng toàn diện.

### Notes

- Mọi thay đổi DTO Backend đều phải đi kèm bước chạy `npm run generate:api` ở `frontend/` (Nguyên tắc XVI).
- Sau khi triển khai lên môi trường thực tế, bắt buộc chạy `uv run alembic upgrade head` và chạy 1 lần `uv run python -m app.scripts.backfill_homework_exercises` (hoặc gọi `POST /api/v1/homeworks/admin/backfill-exercises`) để các bài tập hiện hữu nhận ngay danh mục `homework_exercises` chính thức.
