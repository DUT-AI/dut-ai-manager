# Hợp Đồng API (Phase 1): Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập

**Feature**: `073-rebuild-homework-tracking` | **Date**: 2026-11-18  
**Base URL**: `/api/v1/homeworks`  
**Envelope chuẩn**: `ApiResponse[T]` (`{ is_success, message, data, pagination? }`)  
**Type Synchronization**: Mọi TypeScript type trên `frontend/` sinh tự động từ OpenAPI qua `npm run generate:api` (Nguyên tắc XVI).

---

## 1. DTO Dùng Chung Mới / Mở Rộng

### `HomeworkResponse` (mở rộng giữ tương thích ngược)

```json
{
  "id": 42,
  "title": "Gen2: Xác suất và thống kê",
  "deadline": "2026-11-08T14:00:00Z",
  "link": "https://quiz.dutai.io.vn/lessons/gen2-xstk",
  "slug": "gen2-xstk",
  "requires_coding": true,
  "requires_game": true,
  "last_synced_at": "2026-11-18T01:20:00Z",
  "created_at": "2026-11-01T00:00:00Z",
  "updated_at": "2026-11-18T01:20:00Z",
  "created_by": 1,

  "completion_status": "COMPLETED",
  "timeliness_status": "LATE",
  "completed_at": "2026-11-09T03:15:00Z",
  "is_submitted": true,
  "is_late": true,
  "is_overdue": false,

  "has_coding": true,
  "coding_submitted": true,
  "coding_is_late": true,
  "coding_status": "COMPLETED",
  "total_coding_required": 3,
  "total_coding_completed": 3,

  "has_game": true,
  "game_submitted": true,
  "game_is_late": false,

  "uncompleted_items": []
}
```

**Ngữ nghĩa chuẩn hóa**:
- `completion_status`: `"NOT_STARTED" | "IN_PROGRESS" | "COMPLETED"`
- `timeliness_status`: `"ON_TIME" | "LATE" | "UPCOMING" | "OVERDUE"`
- `is_submitted`: luôn bằng `completion_status === "COMPLETED"` (kể cả khi `timeliness_status === "LATE"`).
- `is_late`: luôn bằng `timeliness_status === "LATE"`.
- `is_overdue`: luôn bằng `timeliness_status === "OVERDUE"` (chưa hoàn thành và đã qua hạn cá nhân).

### `MyHomeworksStats`

```json
{
  "total": 30,
  "completed": 22,
  "completed_on_time": 18,
  "completed_late": 4,
  "uncompleted": 8,
  "overdue": 3
}
```

### `MyHomeworkExerciseStatusDTO`

```json
{
  "exercise_id": "ex-uuid-1",
  "title": "Bài 1: Xác suất có điều kiện",
  "order_index": 1,
  "is_submitted": true,
  "is_passed": true,
  "first_passed_at": "2026-11-07T10:30:00Z",
  "latest_submitted_at": "2026-11-09T08:00:00Z",
  "best_score": 100.0,
  "attempt_count": 2,
  "is_late": false
}
```

---

## 2. Endpoints Học Viên

### 2.1. `GET /api/v1/homeworks/me` (Nâng cấp — Server-Driven Filtering, Search, Stats & Pagination)

- **Auth & Permission**: `CurrentUser`, `HomeworkPermission.READ`
- **Query Parameters**:
  - `page: int = 1` (>= 1)
  - `page_size: int = 20` (1..100)
  - `status: "all" | "uncompleted" | "completed" | "overdue" = "all"`
    - `all`: tất cả bài tập được giao cho user.
    - `uncompleted`: bài có `completion_status in ("NOT_STARTED", "IN_PROGRESS")`.
    - `completed`: bài có `completion_status == "COMPLETED"` (cả `ON_TIME` và `LATE`).
    - `overdue`: bài có `timeliness_status == "OVERDUE"`.
  - `search: str | None = None` (tìm theo `title`, không phân biệt hoa/thường).
- **Response `200 OK`**:
  ```json
  {
    "is_success": true,
    "message": "Success",
    "data": {
      "items": [ /* HomeworkResponse[] */ ],
      "stats": {
        "total": 30,
        "completed": 22,
        "completed_on_time": 18,
        "completed_late": 4,
        "uncompleted": 8,
        "overdue": 3
      }
    },
    "pagination": {
      "page": 1,
      "page_size": 20,
      "total": 8,
      "total_pages": 1
    }
  }
  ```
- **Lưu ý quan trọng**:
  - `stats` luôn tính trên **100%** bài tập được giao cho `current_user` (không phụ thuộc `status`, `search`, `page`).
  - `pagination.total` là tổng số bài khớp bộ lọc `status` + `search`.
  - Đọc hoàn toàn từ DB (không gọi Quiz API), đảm bảo thời gian phản hồi < 1 giây.

### 2.2. `GET /api/v1/homeworks/me/{homework_id}` (Mới — Chi Tiết Bài Tập Cá Nhân Của Học Viên)

- **Auth & Permission**: `CurrentUser`, `HomeworkPermission.READ`
- **Hành vi bảo vệ**:
  - Trả `404 Not Found` nếu bài tập không tồn tại hoặc `current_user` không được giao bài tập này.
- **Response `200 OK`**: `ApiResponse[MyHomeworkDetailResponse]`
  ```json
  {
    "is_success": true,
    "message": "Success",
    "data": {
      "homework": { /* HomeworkResponse với deadline cá nhân & evaluation SSOT của current_user */ },
      "coding_exercises": [ /* MyHomeworkExerciseStatusDTO[] — chỉ gồm các bài con active */ ],
      "submissions": [ /* HomeworkSubmissionDetailResponse[] — lịch sử append-only mới nhất trước */ ]
    }
  }
  ```

### 2.3. `POST /api/v1/homeworks/me/sync` (Mới — Đồng Bộ Nhanh Các Bài Chưa Hoàn Thành Của Học Viên)

- **Auth & Permission**: `CurrentUser`, `HomeworkPermission.READ`
- **Hành vi**:
  - Lọc các bài tập được giao cho `current_user` hiện có `completion_status != COMPLETED` và có `slug` hợp lệ (tối đa 10 bài mỗi lượt, ưu tiên bài mới nhất).
  - Gọi `SyncHomeworkFromQuizUseCase` cho từng bài (fail-safe: lỗi 1 bài không hủy các bài còn lại).
- **Response `200 OK`**: `ApiResponse[SyncMyHomeworksResult]`
  ```json
  {
    "is_success": true,
    "message": "Đã đồng bộ 3/3 bài tập chưa hoàn thành từ Quiz.",
    "data": {
      "total_checked": 3,
      "synced_count": 3,
      "failed_count": 0,
      "results": [ /* SyncHomeworkResult[] */ ],
      "failed_homework_ids": []
    }
  }
  ```

### 2.4. `POST /api/v1/homeworks/{homework_id}/sync` (Giữ nguyên đường dẫn, cập nhật phạm vi & dữ liệu)

- **Auth & Permission**: `CurrentUser`, `HomeworkPermission.READ`
- **Nâng cấp hành vi**:
  - Đồng bộ đồng thời: (1) cờ `requires_coding`/`requires_game`, (2) bảng `homework_exercises` (upsert active + deactivate bài đã gỡ), (3) các lượt nộp Coding & Game với `external_submission_id` và `is_passed` chính xác, (4) cập nhật `homeworks.last_synced_at = now(UTC)`.
- **Response `200 OK`**: `ApiResponse[SyncHomeworkResult]` (bổ sung `last_synced_at: datetime | None`).

---

## 3. Endpoints Báo Cáo, Trang Chủ & Quản Trị

### 3.1. `GET /api/v1/homeworks/report/unsubmitted/{user_id}` & Dashboard `unsubmitted_homeworks`

- **Thay đổi hành vi**:
  - Sử dụng `HomeworkExerciseRepositoryPort` + `Homework.evaluate_submissions()`.
  - Chỉ trả về các bài có `completion_status != "COMPLETED"` (loại bỏ các bài đã hoàn thành 100%, kể cả `COMPLETED + LATE`).
  - Trả về đầy đủ các trường `completion_status`, `timeliness_status`, `total_coding_required`, `total_coding_completed`, `uncompleted_items` trên từng `HomeworkResponse`.

### 3.2. `GET /api/v1/homeworks/report/unsubmitted`

- **Thay đổi hành vi**:
  - Sử dụng `HomeworkExerciseRepositoryPort` + `Homework.evaluate_submissions()` kèm deadline cá nhân của từng `(homework_id, user_id)` thay vì `get_required_exercise_ids_map()`.
  - Đếm `unsubmitted_count` bằng số bài có `completion_status != "COMPLETED"`.

### 3.3. `GET /api/v1/homeworks/{homework_id}/submission-status`

- **Thay đổi hành vi**:
  - Giữ nguyên cấu trúc phản hồi `HomeworkSubmissionStatusResponse` (tương thích ngược tuyệt đối với màn hình quản trị).
  - Nguồn danh mục `coding_exercises`: đọc từ `HomeworkExerciseRepositoryPort` (không gọi live Quiz API).
  - Nguồn đánh giá từng học viên: gọi trực tiếp `homework.evaluate_submissions()` — đảm bảo khớp 100% với trang Học viên.

### 3.4. `POST /api/v1/homeworks/admin/backfill-exercises` (Mới — Admin Backfill)

- **Auth & Permission**: `HomeworkPermission.CREATE`
- **Query Parameters**:
  - `sync_submissions: bool = True` (có đồng bộ luôn bài nộp từ Quiz hay chỉ đồng bộ danh mục `homework_exercises`)
- **Response `200 OK`**: `ApiResponse[BackfillHomeworkExercisesResult]`
  ```json
  {
    "is_success": true,
    "message": "Hoàn tất chuẩn hóa danh mục bài tập con.",
    "data": {
      "total_homeworks": 25,
      "succeeded": 23,
      "skipped_no_slug": 1,
      "failed": 1,
      "failed_details": [
        { "homework_id": 12, "title": "...", "error": "Quiz lesson not found (404)" }
      ]
    }
  }
  ```

---

## 4. Webhook Endpoint

### `POST /api/v1/homeworks/webhook/submission`

- **Header bắt buộc**: `X-Webhook-Secret`
- **Payload**: Giữ nguyên `HomeworkSubmissionWebhookIn` (không phá vỡ Quiz client).
- **Thay đổi hành vi nội bộ**:
  - Gán `external_submission_id` từ `payload.submission_id` (Coding) hoặc `details.session_id` / `payload.submission_id` (Game).
  - Ghi theo chế độ **append-only với idempotent upsert theo `external_submission_id`** — KHÔNG ghi đè lên các lượt nộp trước đó của cùng `(homework_id, user_id, exercise_id)`.
