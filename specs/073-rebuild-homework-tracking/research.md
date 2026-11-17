# Nghiên Cứu Kỹ Thuật (Phase 0): Xây Dựng Lại Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập

**Feature**: `073-rebuild-homework-tracking` | **Date**: 2026-11-18

Tài liệu này tổng hợp các quyết định kiến trúc giải quyết triệt để 5 nguyên nhân gốc rễ khiến hệ thống theo dõi bài tập hiện tại liên tục báo sai trạng thái ("Chưa nộp" / "Chưa làm đủ") dù học viên đã hoàn thành 100% bài tập.

---

## R-001: Tách Bạch Hoàn Toàn Trạng Thái Hoàn Thành Và Tính Đúng Hạn

- **Decision**: Thay thế cách đánh giá gộp (loại bỏ mọi bài nộp trễ ra khỏi `valid_submissions` trong `Homework.evaluate_submissions()`) bằng mô hình đánh giá 2 chiều độc lập:
  1. `CompletionStatus`: `NOT_STARTED` | `IN_PROGRESS` | `COMPLETED` (xét trên toàn bộ lượt nộp đạt `is_passed == True`, không loại bỏ bài nộp sau hạn).
  2. `TimelinessStatus`: `ON_TIME` | `LATE` | `UPCOMING` | `OVERDUE` (so sánh mốc hoàn thành hợp lệ đầu tiên của từng hạng mục với hạn nộp cá nhân `deadline`).
  - Các trường suy diễn chuẩn:
    - `is_submitted = (completion_status == COMPLETED)` -> dùng cho giao diện học viên và lọc "Chưa nộp".
    - `is_completed_on_time = (completion_status == COMPLETED and timeliness_status == ON_TIME)` -> dùng cho kiểm tra vi phạm kỷ luật (`CheckOverdueHomeworkUseCase`).
    - `is_late = (timeliness_status == LATE)`
    - `is_overdue = (timeliness_status == OVERDUE)`
- **Rationale**:
  - Hiện tại `entity.py` (dòng 77-81) lọc `valid_submissions` loại bỏ toàn bộ bài nộp sau hạn. Hệ quả là học viên nộp trễ 1 phút cũng bị biến thành `is_submitted = False` trên Trang chủ và "Bài tập của tôi", trong khi trang Chi tiết và màn hình Quản trị lại không lọc -> gây mâu thuẫn 180 độ giữa các màn hình.
  - Mô hình 2 chiều tương đồng chuẩn LMS quốc tế (Google Classroom, Canvas, Moodle): tách rõ "Đã hoàn thành (Nộp trễ)" khỏi "Chưa nộp / Quá hạn chưa xong", đồng thời bảo toàn hoàn toàn tính nghiêm minh của quy chế phạt vi phạm trễ hạn.
- **Alternatives considered**:
  - *Giữ `is_submitted = False` khi nộp trễ và chỉ thêm cờ `submitted_late`*: Bị loại vì Trang chủ (`HomePage`) và bộ lọc "Chưa nộp" vẫn liệt kê bài đã làm xong vào mục "Chưa nộp", trái trực tiếp với User Story 1 & 2.
  - *Bỏ hoàn toàn xét hạn nộp khi hiển thị lẫn khi xét vi phạm*: Bị loại vì làm hỏng chức năng kiểm tra vi phạm quá hạn kỷ luật (`CheckOverdueHomeworkUseCase`).

---

## R-002: Lưu Trữ Danh Mục Bài Tập Con Chính Thức (`homework_exercises`) Thay Vì Suy Diễn Từ Lịch Sử Nộp Bài

- **Decision**: Tạo bảng quan hệ mới `homework_exercises` gắn trực tiếp với `homeworks` (`homework_id`, `exercise_id`, `title`, `order_index`, `is_active`, timestamps) làm Nguồn Chân Lý Duy Nhất (SSOT) cho danh sách bài tập lập trình bắt buộc của một bài tập.
  - Khởi tạo/cập nhật bảng này tại 3 luồng ghi/đồng bộ: `CreateHomeworkUseCase`, `UpdateHomeworkUseCase`, `SyncHomeworkFromQuizUseCase`.
  - Xóa bỏ hoàn toàn `HomeworkSubmissionRepository.get_required_exercise_ids_map()` và xóa bỏ luồng gọi live Quiz API trong các Use Case đọc (`GetHomeworkDetailUseCase`, `GetHomeworkSubmissionStatusUseCase`, `CheckOverdueHomeworkUseCase`). Tất cả các Use Case đọc cùng đọc từ `HomeworkExerciseRepositoryPort`.
  - Thêm cột `last_synced_at` (TIMESTAMPTZ) vào `homeworks` để hiển thị độ mới của dữ liệu đồng bộ.
- **Rationale**:
  - Hàm `get_required_exercise_ids_map()` hiện tại suy diễn danh sách bài bắt buộc bằng `SELECT DISTINCT exercise_id FROM homework_submissions`. Bất kỳ bản ghi lỗi/di sản nào mang ID giả (`legacy-...`, `sync-...`) hoặc bài tập con đã xóa trên Quiz đều làm phình số lượng bài bắt buộc cho cả lớp -> không ai làm đủ nổi.
  - `GetHomeworkDetailUseCase` và `GetHomeworkSubmissionStatusUseCase` lại gọi live Quiz API qua `HomeworkExerciseResolver`, dẫn đến việc trang học viên và trang quản trị dùng 2 tập bài con khác nhau, đồng thời gây chậm và dễ lỗi khi Quiz API phản hồi chậm.
  - Lưu chính thức trong PostgreSQL giúp toàn bộ luồng đọc đạt < 100ms (dễ dàng thỏa SC-006 < 1 giây), miễn nhiễm với lỗi mạng từ Quiz và miễn nhiễm 100% với bản ghi di sản.
- **Alternatives considered**:
  - *Lưu danh sách bài tập con dưới dạng cột JSON trên `homeworks`*: Bị loại vì khó truy vấn/lọc/join SQL, khó quản lý trạng thái `is_active` theo từng bài con, và kém chuẩn hóa hơn bảng con `homework_exercises`.
  - *Gọi live Quiz API có cache Redis trong mọi luồng đọc*: Bị loại vì vẫn phụ thuộc tính khả dụng của Quiz API khi cache miss, khó đảm bảo nhất quán tuyệt đối với bài tập cũ hoặc bài bị xóa trên Quiz, và làm phức tạp hạ tầng cache invalidation.

---

## R-003: Bảo Toàn Lịch Sử Nộp Bài Bất Biến (Append-Only) Và Khử Trùng Lặp Theo `external_submission_id`

- **Decision**:
  - Thêm cột `external_submission_id` (`VARCHAR(128)`, nullable) vào bảng `homework_submissions` cùng Partial Unique Index `uq_hw_sub_external_id` trên `(homework_id, user_id, submission_type, external_submission_id) WHERE external_submission_id IS NOT NULL`.
  - Sửa `HomeworkSubmissionRepository.find_submission_match()`: **Xóa nhánh match theo `(homework_id, user_id, exercise_id)`** cho bài tập Coding. Chỉ match để idempotent update khi khớp `external_submission_id` (từ `submission_id` của Coding hoặc `session_id` của Game), hoặc fallback khớp chính xác `(homework_id, user_id, submission_type, exercise_id, submitted_at)` cho dữ liệu nguồn cũ không có ID lượt nộp.
  - Khi đánh giá một bài tập con (hoặc phần Game) trong `Homework.evaluate_submissions()`:
    - Trạng thái đạt = tồn tại **ít nhất một** lượt nộp có `is_passed == True`.
    - Mốc hoàn thành hợp lệ để xét đúng hạn (`first_passed_at`) = `min(submitted_at)` của các lượt nộp đạt.
  - Sửa `SyncHomeworkFromQuizUseCase._sync_coding_submissions()`: tôn trọng giá trị `is_passed` / `status` thực tế từ Quiz API thay vì ép cứng `is_passed=True`.
- **Rationale**:
  - Nhánh `find_submission_match` hiện tại tìm Coding theo `(homework_id, user_id, exercise_id)` rồi gọi `update_submission(submitted_at=sub_time)` ghi đè thời gian nộp. Học viên đã nộp đạt đúng hạn, sau hạn nộp lại tối ưu code -> bị ghi đè `submitted_at` thành sau hạn -> thành nộp trễ / chưa nộp / bị phạt oan!
  - Chuyển sang append-only với idempotency theo `external_submission_id` bảo toàn trọn vẹn lịch sử làm bài (đúng tinh thần audit log của bảng `homework_submissions`) và đảm bảo nộp lại sau hạn (dù đạt hay trượt) không bao giờ làm mất thành tích đã đạt trước hạn.
- **Alternatives considered**:
  - *Tiếp tục ghi đè 1 dòng per `(homework_id, user_id, exercise_id)` nhưng chỉ giữ `min(submitted_at)`*: Bị loại vì làm mất lịch sử các lần nộp thực tế của học viên (trái FR-004 và làm hỏng timeline lịch sử nộp bài ở trang Chi tiết).

---

## R-004: Hợp Nhất Hợp Đồng API Cho Học Viên (`GET /homeworks/me`, `GET /homeworks/me/{homework_id}`, `POST /homeworks/me/sync`)

- **Decision**:
  1. Nâng cấp `GET /homeworks/me`:
     - Nhận query parameters: `page`, `page_size`, `status` (`all` | `uncompleted` | `completed` | `overdue`), `search` (tìm không phân biệt hoa thường theo `title`).
     - Trả về `ApiResponse[MyHomeworksPageResponse]` gồm `items: list[HomeworkResponse]` (đã lọc & phân trang), `stats: MyHomeworksStats` (tính trên **100%** bài tập được giao của user, không bị ảnh hưởng bởi `page` hay `status` filter), và `pagination: PaginationMeta` (tính trên tập kết quả sau lọc).
     - Do `zalo-mini-app` không gọi endpoint `/homeworks/me` (đã xác minh qua grep toàn repo) và chỉ có Web Frontend gọi, ta cập nhật trực tiếp Frontend call sites và chạy `npm run generate:api` theo đúng Nguyên tắc X & XVI của Constitution.
  2. Bổ sung `GET /homeworks/me/{homework_id}` (`GetMyHomeworkDetailUseCase`):
     - Trả về `MyHomeworkDetailResponse` chứa thông tin bài tập, **hạn nộp cá nhân** của `current_user`, kết quả đánh giá `SubmissionEvaluation` đầy đủ (bao gồm trạng thái chi tiết từng bài con bắt buộc), và danh sách lịch sử lượt nộp `submissions`.
     - Giải quyết triệt để lỗi hiện tại ở `MyHomeworkDetailPage.tsx` đang dùng `GET /homeworks/{id}` (trả về `min(deadlines)` của cả lớp thay vì deadline cá nhân) và tự tính lại `isCodingCompleted` trên trình duyệt.
  3. Bổ sung `POST /homeworks/me/sync` (`SyncMyUnsubmittedHomeworksUseCase`):
     - Cho phép học viên kích hoạt đồng bộ lại toàn bộ các bài tập chưa đạt `COMPLETED` của chính mình từ Quiz API (tối đa 10 bài mỗi lượt để đảm bảo hiệu năng và tránh quá tải Quiz API), trả về báo cáo số bài đã đồng bộ thành công / thất bại.
- **Rationale**:
  - Tuân thủ triệt để Nguyên tắc XII (Server-Driven Filtering & Pagination Cohesion), Nguyên tắc XIX (SSOT — Frontend không tự tính toán hay ghép 2 API `useMyHomeworks` + `useUnsubmittedByUser`), và Nguyên tắc XVI (OpenAPI Type Sync).
  - Xử lý triệt để trường hợp học viên có > 20 bài tập bị cắt cụt số liệu và mất bài trên trang "Bài tập của tôi".
- **Alternatives considered**:
  - *Giữ `GET /homeworks/me` trả về `list[HomeworkResponse]` và thêm endpoint `GET /homeworks/me/stats` riêng*: Bị loại vì tạo 2 round-trip HTTP không cần thiết và có nguy cơ lệch trạng thái giữa danh sách và số đếm thống kê khi dữ liệu vừa thay đổi.
  - *Tái sử dụng `GET /homeworks/{id}` và bổ sung logic kiểm tra `current_user` trong đó*: Bị loại vì trộn lẫn ngữ cảnh quản trị (cần `assignee_ids`, `min_deadline` toàn lớp cho form chỉnh sửa) với ngữ cảnh học viên (cần `deadline` cá nhân, `evaluation` cá nhân, lịch sử nộp cá nhân) — vi phạm Nguyên tắc VII (Single-Responsibility Use Cases).

---

## R-005: Hợp Nhất `GetHomeworkSubmissionStatusUseCase` Và `CheckOverdueHomeworkUseCase` Vào Cùng SSOT `Homework.evaluate_submissions()`

- **Decision**:
  - Refactor `GetHomeworkSubmissionStatusUseCase`: xóa bỏ logic tính tay `_evaluate_student` hiện tại; thay bằng vòng lặp gọi `homework.evaluate_submissions(user_subs, required_exercises=active_exercises, deadline=assignee.deadline, reference_time=now)` cho từng học viên rồi ánh xạ trực tiếp kết quả sang `StudentHomeworkDetailDTO` và `UserSubmissionInfo`.
  - Refactor `GetUnsubmittedHomeworksForUserUseCase` & `GetUnsubmittedHomeworkReportUseCase`: nạp `active_exercises` từ `HomeworkExerciseRepositoryPort` và lọc bài chưa xong bằng `eval_result.completion_status != CompletionStatus.COMPLETED`.
  - Refactor `CheckOverdueHomeworkUseCase`: nạp `active_exercises` từ `HomeworkExerciseRepositoryPort`, gọi `homework.evaluate_submissions(...)` và chỉ phát `HomeworkOverdueDetected` khi `not eval_result.is_completed_on_time`. Nếu học viên đã hoàn thành nhưng trễ hạn (`completion_status == COMPLETED and timeliness_status == LATE`), lý do vi phạm ghi rõ `"Nộp bài tập trễ hạn (<tên bài tập>)"` thay vì báo sai là `"Chưa hoàn thành ..."`!
- **Rationale**:
  - Đảm bảo 0% sai lệch (SC-002) giữa 4 màn hình (Trang chủ, Bài tập của tôi, Chi tiết bài tập của tôi, Quản trị) và hệ thống kỷ luật tự động.
  - Tuân thủ tuyệt đối Nguyên tắc XIX (Aggregate Root là nơi duy nhất đưa ra quyết định nghiệp vụ).
- **Alternatives considered**:
  - *Chỉ sửa `GetUserHomeworksUseCase` và `GetUnsubmittedHomeworksForUserUseCase`*: Bị loại vì vẫn duy trì 2 bộ logic đánh giá song song, chắc chắn sẽ trôi lệch trở lại trong tương lai.

---

## R-006: Chiến Lược Migration & Backfill Dữ Liệu Hiện Hữu

- **Decision**:
  1. **Alembic Migration** (revision ID: `044_hw_exercises_and_sub_id`, 27 ký tự <= giới hạn 32 ký tự):
     - Tạo bảng `homework_exercises` với unique constraint `(homework_id, exercise_id)` và index `(homework_id, is_active)`.
     - Thêm cột `last_synced_at` (TIMESTAMPTZ, nullable) vào `homeworks`.
     - Thêm cột `external_submission_id` (`VARCHAR(128)`, nullable) vào `homework_submissions`.
     - SQL backfill trong migration: trích xuất `external_submission_id` từ `details->>'submission_id'` (Coding) hoặc `details->>'session_id'` (Game) cho các bản ghi sẵn có; khử các dòng trùng `(homework_id, user_id, submission_type, external_submission_id)` (giữ lại dòng có `is_passed = TRUE` ưu tiên và `submitted_at` sớm nhất); sau đó tạo partial unique index `uq_hw_sub_external_id`.
  2. **Backfill Use Case + CLI Script** (`BackfillHomeworkExercisesUseCase` + `backend/app/scripts/backfill_homework_exercises.py` + Admin endpoint `POST /homeworks/admin/backfill-exercises`):
     - Duyệt toàn bộ `homeworks` hiện có, đồng bộ danh mục bài tập con chính thức `homework_exercises` và các lượt nộp mới nhất từ Quiz API (tái sử dụng `SyncHomeworkFromQuizUseCase`), ghi nhận báo cáo chi tiết (thành công, lỗi/thiếu slug) mà không dừng giữa chừng khi gặp 1 bài tập lỗi.
- **Rationale**:
  - Migration SQL đảm bảo toàn vẹn schema và khử trùng lặp an toàn trước khi bật unique index, có đầy đủ đường `downgrade()`.
  - Tách việc gọi mạng Quiz API ra khỏi Alembic migration (đặt vào script/endpoint backfill riêng) giúp migration DB chạy nhanh, xác định và không bao giờ fail khi deploy nếu Quiz API tạm thời chập chờn.
- **Alternatives considered**:
  - *Gọi HTTP Quiz API trực tiếp bên trong Alembic `upgrade()`*: Bị loại vì anti-pattern nghiêm trọng trong database migration (phụ thuộc mạng ngoài, khóa bảng lâu, không thể rollback sạch).
