# Tasks: Chuẩn hóa Schema và Metadata cho Homework Submission (Coding & Game) - Feature 056

**Feature Branch**: `056-standardize-submission-metadata`  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md) | **Data Model**: [data-model.md](./data-model.md)  
**Created**: 2026-11-08

---

## Task List

### Phase 1: Foundational Backend DTOs (P1) 🎯 MVP Core

- [x] T001 [P1] [US3] Khai báo `CodingScoreDetail` và `CodingSubmissionDetails` Pydantic models trong `backend/app/homework/application/dtos.py`.
- [x] T002 [P1] [US3] Khai báo `GameSubmissionDetails` Pydantic model trong `backend/app/homework/application/dtos.py`.
- [x] T003 [P1] [US3] Cập nhật `HomeworkSubmissionDetailResponse` trong `backend/app/homework/application/dtos.py` đổi trường `details` từ `dict[str, Any]` sang `CodingSubmissionDetails | GameSubmissionDetails` và thêm `@model_validator(mode="before")` để tự động parse từ raw dictionary/model.
- [x] T004 [P1] [US3] Kiểm tra và cập nhật `backend/app/homework/application/get_user_homework_submissions_use_case.py` đảm bảo trả về `HomeworkSubmissionDetailResponse` với `details` có kiểu chuẩn xác.

---

### Phase 2: Webhook & Sync Ingestion Integrity (P2)

- [x] T005 [P2] [US1] Rà soát và cập nhật `backend/app/homework/application/record_submission_use_case.py`: Đảm bảo khi lưu bài nộp Coding hoặc Game từ Webhook, các trường metadata trong `details` tuân thủ đúng tên trường của `CodingSubmissionDetails` và `GameSubmissionDetails`.
- [x] T006 [P2] [US2] Rà soát và cập nhật `backend/app/homework/application/sync_homework_use_case.py`: Đảm bảo `_sync_coding_submissions` và `_sync_game_submissions` đồng bộ `score` vào cả cột DB lẫn metadata `final_score` / `score`.

---

### Phase 3: OpenAPI Contract Export & TypeScript Type Sync (P1)

- [x] T007 [P1] [US3] Xuất OpenAPI schema mới nhất từ FastAPI app ra file `frontend/openapi.json`.
- [x] T008 [P1] [US3] Chạy lệnh `npm run generate:api` tại `frontend/` để cập nhật `frontend/src/types/api.generated.d.ts` với kiểu Tagged Union cho `HomeworkSubmissionDetailResponse.details`.

---

### Phase 4: Frontend Refactoring & Strict Validation (P1)

- [x] T009 [P1] [US1] Tái cấu trúc hàm `normalizeSubmission` trong `frontend/src/features/homework/utils/submissionUtils.ts`: Đọc trực tiếp các trường strongly-typed từ `raw.details` (`original_filename`, `score_details` cho Coding; `correct_count`, `total_questions`, `gold` cho Game), loại bỏ toàn bộ fallback soup và ép kiểu thô.
- [x] T010 [P1] [US1] Cập nhật component `frontend/src/features/homework/components/UnifiedSubmissionTimeline.tsx` để tận dụng autocomplete và type safety từ `NormalizedSubmission` và `raw.details`.
- [x] T011 [P1] [US3] Chạy kiểm tra tĩnh toàn diện `cd frontend && npx tsc -b` (yêu cầu đạt 0 lỗi).
- [x] T012 [P1] [US3] Chạy đóng gói production `cd frontend && npm run build` (`tsc -b && vite build`) để xác nhận không có lỗi runtime/build.
