# Hướng Dẫn Xác Thực Nhanh (Quickstart): Hệ Thống Theo Dõi Trạng Thái Hoàn Thành Bài Tập

**Feature**: `073-rebuild-homework-tracking` | **Date**: 2026-11-18  
**Tài liệu tham chiếu**: [spec.md](spec.md) · [data-model.md](data-model.md) · [contracts/api-contracts.md](contracts/api-contracts.md)

---

## 1. Điều Kiện Tiên Quyết

- Backend Python 3.12+ (môi trường ảo tại `backend/.venv` hoặc `uv`).
- PostgreSQL đang hoạt động và cấu hình `DATABASE_URL`, `QUIZ_API_URL`, `QUIZ_WEBHOOK_SECRET` trong `backend/.env`.
- Frontend Node.js 20+ đã cài dependencies tại `frontend/`.

---

## 2. Chạy Migration & Chuẩn Hóa Dữ Liệu Hiện Có

```bash
# 1. Áp dụng Alembic migration tạo bảng homework_exercises, thêm last_synced_at & external_submission_id
cd backend
uv run alembic upgrade head

# 2. Chạy script backfill một lần để đồng bộ danh mục bài tập con chính thức từ Quiz API
uv run python -m app.scripts.backfill_homework_exercises
```

**Kết quả kỳ vọng**:
- Migration hoàn tất không lỗi; bảng `homework_exercises` được tạo và partial unique index `uq_hw_sub_external_id` hoạt động.
- Script backfill in báo cáo tổng số bài tập đã chuẩn hóa thành công danh mục bài con (`succeeded`), danh sách bỏ qua hoặc lỗi (nếu có) để admin xử lý.

---

## 3. Kiểm Thử Tự Động (Backend & Frontend)

### 3.1. Backend Unit, Integration & API Tests

```bash
cd backend
# Kiểm tra lint + quy tắc UTC (DTZ)
uv run ruff check app/homework tests/unit/homework tests/integration/homework tests/api/homework

# Chạy toàn bộ test suite của phân hệ homework
uv run pytest tests/unit/homework tests/integration/homework tests/api/homework -v
```

**Kịch bản bắt buộc phải pass 100%**:
1. **Nộp trễ 100% (`COMPLETED + LATE`)**: `is_submitted == True`, `is_late == True`, `is_overdue == False`, `is_completed_on_time == False`; không xuất hiện trong `GetUnsubmittedHomeworksForUserUseCase`; `CheckOverdueHomeworkUseCase` vẫn phát hiện vi phạm nộp trễ.
2. **Nộp đúng hạn rồi nộp lại sau hạn**: `first_passed_at <= deadline` -> vẫn giữ `COMPLETED + ON_TIME`, `is_completed_on_time == True`; cả 2 lượt nộp đều còn trong lịch sử; không bị ghi nhận vi phạm.
3. **Lịch sử có bản ghi lỗi/di sản (`legacy-...`, `sync-...`, bài con bị gỡ `is_active=False`)**: Không làm tăng `total_coding_required`; học viên làm đủ các bài con `is_active=True` đạt `COMPLETED`.
4. **Đồng nhất 4 luồng**: `GetUserHomeworksUseCase`, `GetMyHomeworkDetailUseCase`, `GetUnsubmittedHomeworksForUserUseCase`, `GetHomeworkSubmissionStatusUseCase` trả về cùng trạng thái hoàn thành và tiến độ cho cùng `(user_id, homework_id)`.
5. **Server-driven filter & pagination**: Với 30 bài tập, `GET /api/v1/homeworks/me?page=2&page_size=20&status=all` trả đúng 10 bài còn lại, `stats` giữ nguyên tổng 30; lọc `status=uncompleted` và `search=...` tìm được bài ở trang 2.
6. **Idempotent Webhook & Sync**: Gửi lặp cùng `external_submission_id` không tạo bản ghi trùng; gửi 2 `external_submission_id` khác nhau cho cùng `exercise_id` tạo 2 bản ghi riêng biệt.

### 3.2. Sinh Kiểu OpenAPI & Build Frontend

```bash
# Đảm bảo backend chạy ở cổng 8001 (hoặc cập nhật từ schema mới nhất)
cd frontend
npm run generate:api
npm run lint
npm run build
```

**Kết quả kỳ vọng**: `tsc -b` và `vite build` thành công với 0 lỗi TypeScript và 0 lỗi ESLint.

---

## 4. Xác Thực End-to-End Trên Trình Duyệt

1. **Trang chủ (`/dashboard`)**:
   - Đăng nhập bằng tài khoản học viên đã làm xong toàn bộ bài tập (kể cả các bài nộp sau hạn).
   - Xác minh mục **"Bài tập chưa nộp"** trống và hiển thị thông báo chúc mừng; không còn danh sách thẻ đỏ "Chưa nộp" như trước.
2. **Trang Bài tập của tôi (`/dashboard/my-homeworks`)**:
   - Xác minh các thẻ bài tập đã nộp đủ đúng hạn hiện **"Đã hoàn thành • Đúng hạn"** (xanh lá); các bài nộp đủ sau hạn hiện **"Đã hoàn thành • Nộp trễ"** (không báo "Chưa nộp" hay "Chưa làm đủ").
   - Chuyển đổi giữa các tab `Tất cả` / `Chưa hoàn thành` / `Đã hoàn thành` / `Quá hạn`, nhập từ khóa tìm kiếm và chuyển trang: xác minh số đếm trên 4 thẻ thống kê không bị sai lệch và kết quả phản hồi từ Backend.
   - Nhấn nút **"Đồng bộ từ Quiz"**: xác minh trạng thái và mốc `last_synced_at` cập nhật ngay, đồng thời dữ liệu Trang chủ được làm mới theo.
3. **Trang Chi tiết bài tập của tôi (`/dashboard/my-homeworks/:id`)**:
   - Xác minh hạn nộp hiển thị là **hạn nộp cá nhân** của học viên (đặc biệt với học viên được gia hạn).
   - Xác minh danh sách bài tập con bắt buộc và trạng thái tổng thể khớp 100% với thẻ ngoài trang danh sách và màn hình quản trị.
