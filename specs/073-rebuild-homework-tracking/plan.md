# Implementation Plan: Xây Dựng Lại Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập Học Viên

**Branch**: `073-rebuild-homework-tracking` | **Date**: 2026-11-18 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/073-rebuild-homework-tracking/spec.md`

---

## Summary

Đập đi xây lại toàn bộ cơ chế xác định danh mục bài tập bắt buộc, lưu vết lượt nộp bài, đánh giá trạng thái hoàn thành bài tập và hiển thị trên giao diện học viên nhằm chấm dứt triệt để tình trạng học viên đã làm đủ bài nhưng vẫn bị báo "Chưa nộp" hoặc "Chưa làm đủ".

Giải pháp tập trung vào 5 thay đổi kiến trúc cốt lõi (chi tiết tại [research.md](research.md), [data-model.md](data-model.md), [contracts/api-contracts.md](contracts/api-contracts.md)):

1. **Danh mục bài tập con chính thức (`homework_exercises`)**: Lưu tường minh các bài tập lập trình bắt buộc từ Quiz API gắn với `Homework` (có `is_active` và `homeworks.last_synced_at`), **xóa vĩnh viễn** hàm suy diễn sai lệch `get_required_exercise_ids_map()` và xóa các lời gọi live Quiz API trong luồng đọc.
2. **Đánh giá 2 chiều độc lập trên Aggregate Root SSOT**: Nâng cấp `Homework.evaluate_submissions()` trả về đồng thời `CompletionStatus` (`NOT_STARTED` / `IN_PROGRESS` / `COMPLETED`) và `TimelinessStatus` (`ON_TIME` / `LATE` / `UPCOMING` / `OVERDUE`), tách biệt bài đã hoàn thành trễ hạn (`COMPLETED + LATE`) khỏi "Chưa nộp", đồng thời cung cấp `is_completed_on_time` cho job kiểm tra vi phạm kỷ luật.
3. **Lịch sử nộp bài bất biến (Append-Only) với `external_submission_id`**: Ngừng ghi đè `submitted_at` theo `(homework_id, user_id, exercise_id)`; khử trùng lặp qua partial unique index theo `external_submission_id`; lấy mốc `min(submitted_at)` trong các lượt `is_passed=True` để xét đúng hạn nên nộp lại sau hạn không bao giờ làm mất trạng thái Đúng hạn.
4. **Hợp nhất 100% 4 màn hình & 6 Use Case vào một SSOT**: `GetUserHomeworksUseCase` (kèm server-driven filter/search/pagination/stats), `GetMyHomeworkDetailUseCase` (MỚI — dùng đúng hạn nộp cá nhân), `GetUnsubmittedHomeworksForUserUseCase`, `GetUnsubmittedHomeworkReportUseCase`, `GetHomeworkSubmissionStatusUseCase` và `CheckOverdueHomeworkUseCase` đều gọi trực tiếp `Homework.evaluate_submissions()`.
5. **Frontend hiển thị thuần túy + Backfill chuẩn hóa dữ liệu cũ**: Loại bỏ toàn bộ logic tự tính trạng thái và lời gọi kép `useUnsubmittedByUser` trên `MyHomeworkPage`, tách component rõ ràng, sinh types tự động qua `openapi-typescript`, và chạy migration + script backfill một lần cho dữ liệu hiện hữu.

---

## Technical Context

**Language/Version**: Backend Python >= 3.12 · Frontend TypeScript 5.9.3 (React 19.2.0)

**Primary Dependencies**:
- Backend: FastAPI >= 0.128, SQLAlchemy / SQLModel >= 0.0.38, Pydantic v2 >= 2.12.5, Alembic >= 1.17.2, Dishka >= 1.9.1, httpx, Loguru, Ruff
- Frontend: Vite 7.2.4, Ant Design 6.1.4, TanStack React Query 5.90.19, Axios 1.13.2, React Router 7.11.0, Tailwind CSS 4.1.18, `openapi-typescript` 7.13.0

**Storage**: PostgreSQL (SQLAlchemy ORM + Alembic migrations, lưu trữ TIMESTAMPTZ UTC)

**Testing**: Backend `pytest` + `pytest-asyncio` (unit in-memory, integration, API) + `ruff check` (kèm rule `DTZ`) · Frontend `npm run lint`, `npm run build` (`tsc -b && vite build`), Playwright E2E

**Target Platform**: Linux server (Docker/Uvicorn) + Modern Web Browser (Desktop & Mobile responsive)

**Project Type**: Web application (Monorepo gồm `backend/`, `frontend/`, `zalo-mini-app/`)

**Performance Goals**: Thời gian phản hồi `GET /api/v1/homeworks/me` < 1 giây (mục tiêu p95 < 200ms nhờ 100% DB-first, 0 lời gọi live Quiz API trên luồng đọc)

**Constraints**:
- Tuân thủ tuyệt đối `DUT AI Manager Constitution v1.14.0` (19 nguyên tắc)
- Alembic Revision ID <= 32 ký tự (`044_hw_exercises_and_sub_id`)
- Zero naive datetime (`DTZ` enforced)
- Không ảnh hưởng ngược tới `zalo-mini-app` và màn hình quản trị hiện có

**Scale/Scope**: ~100–500 học viên, ~20–200 bài tập, hàng nghìn lượt nộp bài; ảnh hưởng 1 bounded context chính (`homework`), 1 trang dashboard (`HomePage`), 2 trang học viên (`MyHomeworkPage`, `MyHomeworkDetailPage`) và 1 job kiểm tra vi phạm

---

## Constitution Check

*GATE: Đánh giá cả trước Phase 0 và sau Phase 1 design theo `.specify/memory/constitution.md` (v1.14.0).*

| Nguyên tắc | Yêu cầu cổng kiểm soát | Trước Design | Sau Phase 1 | Ghi chú tuân thủ |
|---|---|---|---|---|
| **I. Clean Architecture & Practical DDD** | Tách rõ `domain/` (pure), `application/`, `infrastructure/`, `controller.py` | PASS | PASS | `HomeworkExercise`, `CompletionStatus`, `TimelinessStatus`, `ExerciseEvaluation`, `Homework.evaluate_submissions()` thuần Domain; `HomeworkExerciseRepositoryPort` tại `domain/ports/`. |
| **II. Dishka DI** | Đăng ký mọi repo & use case trong `providers.py`, không khởi tạo trực tiếp | PASS | PASS | Đăng ký `HomeworkExerciseRepository`, `HomeworkExerciseRepositoryPort`, `GetMyHomeworkDetailUseCase`, `SyncMyUnsubmittedHomeworksUseCase`, `BackfillHomeworkExercisesUseCase` trong `HomeworkModuleProvider`. |
| **III. Enterprise UTC Storage** | Mọi cột datetime dùng `TIMESTAMPTZ`, `datetime.now(UTC)`, `ensure_utc()` | PASS | PASS | `homework_exercises.created_at/updated_at`, `homeworks.last_synced_at`, `first_passed_at` toàn bộ timezone-aware UTC; vượt qua Ruff `DTZ`. |
| **IV. Event-Driven Decoupling** | Side effect gửi thông báo / kỷ luật qua `EventBus` | PASS | PASS | `CheckOverdueHomeworkUseCase` tiếp tục publish `HomeworkOverdueDetected` qua `EventBus`. |
| **V. API Backward Compatibility & Non-Null DTOs** | Envelope `ApiResponse[T]`, trường quan hệ không null đột ngột | PASS | PASS | `HomeworkResponse` giữ đủ field cũ + bổ sung field mới có giá trị xác định; `zalo-mini-app` không gọi `/homeworks/me`. |
| **VI. Idempotency & Resilience** | Chống trùng lặp khi webhook/sync chạy lại | PASS | PASS | Partial unique index `uq_hw_sub_external_id` trên `(homework_id, user_id, submission_type, external_submission_id)`. |
| **VII. Single-Responsibility Use Cases** | 1 file `*_use_case.py` = 1 class = 1 public `execute()`, export trong `__init__.py` | PASS | PASS | Tách riêng `get_my_homework_detail_use_case.py`, `sync_my_unsubmitted_homeworks_use_case.py`, `backfill_homework_exercises_use_case.py`. |
| **VIII. Frontend Component Modularity** | Page chỉ làm orchestrator; tách subcomponents; pagination chuẩn | PASS | PASS | Tách `MyHomeworkStatsCards.tsx`, `MyHomeworkFilterBar.tsx`, `HomeworkCard.tsx`, `MyHomeworkExerciseList.tsx`; phân trang `defaultPageSize: 20`, `pageSizeOptions`, `showSizeChanger`, `showTotal`. |
| **IX. Pure Composition** | Không tạo Base Use Case | PASS | PASS | Các Use Case inject trực tiếp repo ports và gọi `Homework.evaluate_submissions()`. |
| **X. Zero Redundant Backward Compatibility** | Xóa bỏ hàm/alias lỗi thời, refactor call sites trực tiếp | PASS | PASS | Xóa hẳn `get_required_exercise_ids_map()`, xóa `HomeworkExerciseResolver` gọi live Quiz API trên luồng đọc, xóa gọi `useUnsubmittedByUser` trên `MyHomeworkPage.tsx`. |
| **XI. Plain Text Notifications** | Không raw markdown trong nội dung thông báo | PASS | PASS | Lý do vi phạm (`reason_msg`) là plain text sạch. |
| **XII. Server-Driven Filtering & Pagination** | Không lọc client-side trên trang server; reset `page=1` khi đổi filter | PASS | PASS | `GET /homeworks/me` nhận `status`, `search`, `page`, `page_size` từ Backend; đổi tab/search reset về trang 1. |
| **XIII & XVII. Strongly-Typed Storage** | Không dùng `dict[str, Any]` raw trong ORM/Entity | PASS | PASS | Giữ nguyên `SubmissionDetailsJSON` TypeDecorator; `HomeworkExercise` & `ExerciseEvaluation` định kiểu tĩnh hoàn toàn bằng Pydantic. |
| **XIV. No Fake Optionals & Fail-Fast** | Collaborator bắt buộc không được `Type | None = None` | PASS | PASS | `homework_exercise_repo: HomeworkExerciseRepositoryPort` là tham số bắt buộc ở tất cả Use Case liên quan. |
| **XV. Unified Client Networking** | Chỉ dùng `axiosInstance` | PASS | PASS | Mọi hàm mới đi qua `homeworkService` sử dụng `axiosInstance`. |
| **XVI. OpenAPI SSOT & Type Sync** | Chạy `npm run generate:api`, không viết tay interface API | PASS | PASS | Cập nhật `frontend/src/features/homework/types/homework.types.ts` tham chiếu trực tiếp `Schema<...>` từ `api.generated.d.ts`. |
| **XIX. SSOT & Zero Fallback Logic** | Aggregate Root là nơi duy nhất đánh giá; cấm dual-path fallback | PASS | PASS | Cả 6 Use Case gọi chung `Homework.evaluate_submissions()`; không còn nhánh fallback suy diễn bài con từ `homework_submissions`. |
| **Migration Gate** | Revision ID <= 32 ký tự, có `upgrade()` & `downgrade()` | PASS | PASS | `044_hw_exercises_and_sub_id` (27 ký tự), có `upgrade()` và `downgrade()` đầy đủ. |

**Gate Result**: **PASS (19/19)** — Không có vi phạm nào cần ngoại lệ.

---

## Project Structure

### Documentation (this feature)

```text
specs/073-rebuild-homework-tracking/
├── spec.md                       # Đặc tả nghiệp vụ (/speckit-specify)
├── checklists/
│   └── requirements.md           # Checklist chất lượng đặc tả (16/16 pass)
├── plan.md                       # Tài liệu này (/speckit-plan)
├── research.md                   # Quyết định kỹ thuật & phân tích đánh đổi (Phase 0)
├── data-model.md                 # Schema DB, Domain Entities, State Transitions (Phase 1)
├── contracts/
│   └── api-contracts.md          # Hợp đồng REST API & DTOs (Phase 1)
├── quickstart.md                 # Hướng dẫn migration, backfill & xác thực E2E (Phase 1)
└── tasks.md                      # Danh sách task triển khai (/speckit-tasks - chưa tạo ở bước này)
```

### Source Code (repository root)

```text
backend/
├── alembic/versions/
│   └── 044_hw_exercises_and_sub_id.py                                  # [NEW] Bảng homework_exercises, last_synced_at, external_submission_id + dedup + unique index
├── app/
│   ├── scripts/
│   │   └── backfill_homework_exercises.py                              # [NEW] CLI script backfill một lần từ Quiz API
│   └── homework/
│       ├── controller.py                                               # [MODIFY] Nâng cấp GET /me; thêm GET /me/{id}, POST /me/sync, POST /admin/backfill-exercises
│       ├── providers.py                                                # [MODIFY] Đăng ký HomeworkExerciseRepository + 3 Use Case mới; gỡ HomeworkExerciseResolver
│       ├── domain/
│       │   ├── entity.py                                               # [MODIFY] Thêm HomeworkExercise, last_synced_at, external_submission_id; viết lại Homework.evaluate_submissions() 2 chiều
│       │   ├── value_objects.py                                        # [MODIFY] Thêm CompletionStatus, TimelinessStatus, ExerciseEvaluation; nâng cấp SubmissionEvaluation
│       │   └── ports/
│       │       ├── __init__.py                                         # [MODIFY] Export HomeworkExerciseRepositoryPort
│       │       ├── homework_exercise_repository_port.py                # [NEW] Port quản lý danh mục bài con chính thức
│       │       └── homework_submission_repository_port.py              # [MODIFY] Xóa get_required_exercise_ids_map(), chuẩn hóa find_submission_match()
│       ├── infrastructure/
│       │   ├── model.py                                                # [MODIFY] Thêm HomeworkExerciseModel, Homeworks.last_synced_at, HomeworkSubmissions.external_submission_id
│       │   ├── homework_exercise_repository.py                         # [NEW] SQLAlchemy implementation của HomeworkExerciseRepositoryPort
│       │   ├── homework_repository.py                                  # [MODIFY] Cập nhật last_synced_at; hỗ trợ truy vấn bài được giao kèm filter/search
│       │   ├── homework_submission_repository.py                       # [MODIFY] Bỏ match ghi đè theo exercise_id; ưu tiên external_submission_id; xóa get_required_exercise_ids_map()
│       │   └── in_memory/
│       │       ├── __init__.py                                         # [MODIFY] Export InMemoryHomeworkExerciseRepository
│       │       ├── in_memory_exercise_repo.py                          # [NEW] In-memory implementation cho unit test
│       │       └── in_memory_submission_repo.py                        # [MODIFY] Đồng bộ hành vi append-only & xóa get_required_exercise_ids_map()
│       └── application/
│           ├── __init__.py                                             # [MODIFY] Export các Use Case mới, gỡ HomeworkExerciseResolver
│           ├── homework_exercise_resolver.py                           # [DELETE] Không còn suy diễn/gọi live Quiz API trên luồng đọc
│           ├── dtos/
│           │   ├── __init__.py                                         # [MODIFY] Export các DTO mới
│           │   ├── homework_dtos.py                                    # [MODIFY] Mở rộng HomeworkResponse; thêm MyHomeworksStats, MyHomeworksPageResponse, MyHomeworkDetailResponse, SyncMyHomeworksResult, BackfillHomeworkExercisesResult
│           │   └── submission_dtos.py                                  # [MODIFY] Thêm MyHomeworkExerciseStatusDTO
│           ├── create_homework_use_case.py                             # [MODIFY] Đồng bộ homework_exercises từ Quiz ngay khi tạo
│           ├── update_homework_use_case.py                             # [MODIFY] Đồng bộ homework_exercises khi đổi slug/requires_coding
│           ├── sync_homework_use_case.py                               # [MODIFY] Upsert homework_exercises (active/inactive), tôn trọng is_passed, lưu external_submission_id, cập nhật last_synced_at
│           ├── record_submission_use_case.py                           # [MODIFY] Lưu external_submission_id, append-only idempotent không ghi đè mốc cũ
│           ├── get_user_homeworks_use_case.py                          # [MODIFY] Đọc homework_exercises, đánh giá SSOT, trả về stats tổng + lọc status/search + phân trang server-side
│           ├── get_my_homework_detail_use_case.py                      # [NEW] Chi tiết bài tập cá nhân kèm deadline cá nhân, evaluation & submissions
│           ├── sync_my_unsubmitted_homeworks_use_case.py               # [NEW] Học viên tự đồng bộ nhanh các bài chưa hoàn thành từ Quiz
│           ├── backfill_homework_exercises_use_case.py                 # [NEW] Chuẩn hóa dữ liệu bài tập hiện có từ Quiz API
│           ├── get_homework_detail_use_case.py                         # [MODIFY] Đọc coding_exercises từ HomeworkExerciseRepositoryPort
│           ├── get_homework_submission_status_use_case.py              # [MODIFY] Xóa logic _evaluate_student viết tay, gọi thẳng Homework.evaluate_submissions()
│           ├── get_unsubmitted_homeworks_for_user_use_case.py          # [MODIFY] Lọc theo completion_status != COMPLETED dùng HomeworkExerciseRepositoryPort
│           ├── get_unsubmitted_homework_report_use_case.py             # [MODIFY] Đếm theo completion_status != COMPLETED dùng HomeworkExerciseRepositoryPort + deadline cá nhân
│           ├── check_overdue_homework_use_case.py                      # [MODIFY] Dùng HomeworkExerciseRepositoryPort & xét is_completed_on_time
│           └── rescan_all_homeworks_use_case.py                        # [MODIFY] Cập nhật dependency sang HomeworkExerciseRepositoryPort
└── tests/
    ├── fixtures/homework_fixtures.py                                   # [MODIFY] Bổ sung factory cho HomeworkExercise và multi-attempt submissions
    ├── unit/homework/
    │   ├── test_homework_pure_domain.py                                # [MODIFY] Bao phủ đủ ma trận 2 chiều (ON_TIME, LATE, UPCOMING, OVERDUE, resubmit sau hạn, fail sau pass, legacy/inactive exercises)
    │   ├── test_homework_ssot.py                                       # [MODIFY] Kiểm chứng đồng nhất 100% giữa 4 Use Case đọc & CheckOverdueHomeworkUseCase
    │   ├── test_get_user_homeworks.py                                  # [MODIFY] Kiểm chứng stats tổng, lọc status, search, phân trang >20 bài
    │   ├── test_get_my_homework_detail.py                              # [NEW] Kiểm chứng deadline cá nhân & từ chối 404 khi không phải assignee
    │   ├── test_homework_in_memory_use_cases.py                        # [MODIFY] Cập nhật dùng InMemoryHomeworkExerciseRepository
    │   ├── test_homework_ports_contract.py                             # [MODIFY] Thêm contract test cho HomeworkExerciseRepositoryPort
    │   ├── test_homework_checker.py                                    # [MODIFY] Kiểm chứng nộp đúng hạn + nộp lại sau hạn không phạt; nộp trễ vẫn phạt với lý do rõ ràng
    │   └── test_get_homework_detail_use_case.py                        # [MODIFY] Cập nhật sang HomeworkExerciseRepositoryPort
    └── integration/homework/
        ├── test_homework_webhook.py                                    # [MODIFY] Kiểm chứng append-only theo external_submission_id không ghi đè submitted_at cũ
        └── test_homework_quiz_integration.py                           # [MODIFY] Kiểm chứng sync cập nhật homework_exercises (active/inactive) và tôn trọng is_passed

frontend/src/
├── types/api.generated.d.ts                                            # [REGENERATE] Sinh qua npm run generate:api
├── pages/HomePage.tsx                                                  # [MODIFY] Hiển thị đúng nhãn trạng thái (Chưa nộp / Làm dở / Quá hạn) & điều hướng click sang chi tiết bài tập
└── features/homework/
    ├── types/homework.types.ts                                         # [MODIFY] Dùng Schema<...> cho MyHomeworksPageResponse, MyHomeworkDetailResponse, SyncMyHomeworksResult
    ├── services/homework.service.ts                                    # [MODIFY] Cập nhật getMyHomeworks(params); thêm getMyHomeworkDetail(id), syncMyUnsubmitted()
    ├── hooks/useHomeworks.ts                                           # [MODIFY] Cập nhật useMyHomeworks(params); thêm useMyHomeworkDetail(id), useSyncMyUnsubmitted(); invalidate cả ['dashboard'] khi sync
    ├── pages/
    │   ├── MyHomeworkPage.tsx                                          # [MODIFY] Orchestrator thuần: bỏ useUnsubmittedByUser, dùng server-driven filter/search/pagination, thêm nút Đồng bộ từ Quiz
    │   └── MyHomeworkDetailPage.tsx                                    # [MODIFY] Chuyển sang useMyHomeworkDetail(id), xóa toàn bộ logic tự tính hoàn thành trên client, hiển thị deadline cá nhân
    └── components/
        ├── index.ts                                                    # [MODIFY] Export các subcomponents mới
        ├── HomeworkCard.tsx                                            # [MODIFY] Render thuần theo completion_status & timeliness_status (hiển thị "Đã hoàn thành • Nộp trễ", bỏ tự suy luận)
        ├── MyHomeworkStatsCards.tsx                                    # [NEW] 4 thẻ thống kê từ server stats (có hiển thị chi tiết đúng hạn / nộp trễ)
        ├── MyHomeworkFilterBar.tsx                                     # [NEW] Thanh tab lọc + ô tìm kiếm debounce + reset page=1
        └── MyHomeworkExerciseChecklist.tsx                             # [NEW] Bảng tiến độ từng bài tập con bắt buộc từ Backend trên trang chi tiết học viên
```

**Structure Decision**: Dự án theo cấu trúc Web Application Monorepo (`backend/` + `frontend/`). Mọi thay đổi Backend đóng gói gọn trong bounded context `backend/app/homework/` (và 1 file migration Alembic + 1 script backfill); Frontend tập trung trong `frontend/src/features/homework/` và 1 điểm hiển thị tại `frontend/src/pages/HomePage.tsx`. Không đụng vào `zalo-mini-app/` vì đã xác minh không có lời gọi tới các endpoint bị thay đổi cấu trúc.

---

## Rollout & Risk Mitigation Strategy

1. **Thứ tự triển khai an toàn**:
   - Bước 1: Alembic migration `044_hw_exercises_and_sub_id` (tạo bảng `homework_exercises`, thêm cột `last_synced_at` & `external_submission_id`, khử trùng lặp và tạo partial unique index).
   - Bước 2: Domain Layer (`HomeworkExercise`, `CompletionStatus`, `TimelinessStatus`, `ExerciseEvaluation`, `Homework.evaluate_submissions()`) + bộ Unit Test pure domain đạt 100% pass.
   - Bước 3: Infrastructure Repositories (SQLAlchemy + InMemory) & Dishka Providers.
   - Bước 4: Application Use Cases (Write/Sync -> Read -> Overdue Checker -> Backfill) + Controller endpoints + toàn bộ pytest suite đạt 100% pass.
   - Bước 5: Chạy `npm run generate:api` đồng bộ OpenAPI types -> cập nhật Frontend (`MyHomeworkPage`, `HomeworkCard`, `MyHomeworkDetailPage`, `HomePage`) -> kiểm tra `npm run lint` & `npm run build`.
   - Bước 6: Khi deploy lên production/staging: chạy `alembic upgrade head`, ngay sau đó chạy `python -m app.scripts.backfill_homework_exercises` (hoặc gọi `POST /api/v1/homeworks/admin/backfill-exercises`) để điền danh mục bài tập con chính thức cho toàn bộ bài tập đang có.
2. **Xử lý rủi ro dữ liệu cũ khi bài tập không còn trên Quiz**:
   - Nếu một bài tập quá cũ trả `404` khi backfill từ Quiz, script ghi nhận vào `failed_details` và bỏ qua an toàn; với bài tập có `homework_exercises` rỗng nhưng `requires_coding=True`, `Homework.evaluate_submissions()` áp dụng nhánh fallback xác định duy nhất (≥ 1 lượt Coding `is_passed=True` là hoàn thành), không làm treo hệ thống hay biến học viên đã nộp thành chưa nộp.
3. **Bảo vệ hiệu năng khi học viên bấm "Đồng bộ từ Quiz"**:
   - Endpoint `POST /homeworks/me/sync` chỉ đồng bộ tối đa 10 bài chưa hoàn thành của chính học viên đó mỗi lần bấm và chạy tuần tự fail-safe, tránh gửi bão request tới Quiz API.

---

## Complexity Tracking

> Không có vi phạm Constitution nào phát sinh trong thiết kế. Bảng dưới đây giữ trống theo hướng dẫn.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| *Không có* | — | — |
