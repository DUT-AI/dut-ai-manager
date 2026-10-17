# Implementation Plan: Chuẩn Hóa Kiểm Tra Bài Nộp Qua Database & Bổ Sung Nút Sync Thủ Công (My Homeworks)

**Branch**: `013-fix-my-homeworks-coding-submitted` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)

**Input**: Đặc tả từ `/specs/013-fix-my-homeworks-coding-submitted/spec.md` chuyển đổi cơ chế đọc trạng thái bài nộp sang DB-First (loại bỏ HTTP runtime Quiz API trong các endpoint GET) và bổ sung nút Sync cho học viên trên giao diện.

---

## 1. Summary

Chuyển đổi hoàn toàn cơ chế kiểm tra trạng thái nộp bài (`coding_submitted`, `game_submitted`, `is_submitted`) trong `GetHomeworksUseCase.get_assigned_to_user` (`GET /api/v1/homeworks/me`) và `get_unsubmitted_report` sang truy vấn cơ sở dữ liệu nội bộ (`homework_submissions`). Loại bỏ 100% các cuộc gọi HTTP runtime sang Quiz API trong luồng đọc dữ liệu, triệt tiêu hoàn toàn lỗi chập chờn true/false do timeout 5s. Đồng thời, mở rộng quyền của endpoint `POST /api/v1/homeworks/{id}/sync` để học viên có thể tự đồng bộ bài của mình, và tích hợp nút bấm **"Đồng bộ kết quả"** (Sync) trực tiếp trên từng thẻ bài tập (`HomeworkCard`) ở giao diện Frontend.

---

## 2. Technical Context

- **Language/Version**: Python 3.12 (Backend), TypeScript / React 19 (Frontend)
- **Primary Dependencies**: FastAPI, Dishka, SQLAlchemy 2.0, Ant Design 5.x, Axios / TanStack Query
- **Storage**: PostgreSQL (Bảng `homeworks`, `homework_submissions`)
- **Testing**: PyTest (`pytest backend/tests/api/test_homework_api.py`), Jest/Build validation (`npm run build`)
- **Target Platform**: Docker / Linux Server & Web Browser (DUT AI Manager)
- **Performance Goals**: Giảm độ trễ API `/homeworks/me` từ 1000-5000ms xuống < 50ms (Zero external HTTP blocking)
- **Constraints**: 
  - Không phá vỡ cấu trúc Response Model (`HomeworkResponse`).
  - Tuân thủ Constitution Principle I (Clean Architecture), Principle VII (Modular Use Cases), Principle VIII (Modular UI Components).
- **Scale/Scope**: 2 use cases backend (`GetHomeworksUseCase`, `SyncHomeworkFromQuizUseCase`), 1 controller endpoint, 2 component frontend (`HomeworkCard.tsx`, `MyHomeworkPage.tsx`).

---

## 3. Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái | Ghi chú |
| :--- | :--- | :---: | :--- |
| **Principle I: Clean Architecture** | Tầng Application chỉ truy vấn qua `HomeworkRepository` và gọi `SyncHomeworkFromQuizUseCase`. | **PASS** | Tách bạch rõ ranh giới tầng dữ liệu và nghiệp vụ. |
| **Principle II: Dependency Injection** | Sử dụng Dishka để inject `HomeworkRepository`. | **PASS** | Đã được đăng ký sẵn trong `HomeworkModuleProvider`. |
| **Principle III: Unified UTC+7** | So sánh deadline và hạn nộp dựa trên timezone UTC+7. | **PASS** | Sử dụng `get_current_utc7_time()`. |
| **Principle V: API Backward Compatibility** | Giữ nguyên schema `HomeworkResponse` (`is_submitted`, `coding_submitted`, `game_submitted`). | **PASS** | 100% tương thích hợp đồng API. |
| **Principle VI: Idempotency & Network Resilience** | Cơ chế Sync và webhook hỗ trợ dedup / upsert submission. | **PASS** | `find_submission_match` trong repository ngăn chặn bản ghi trùng lặp. |
| **Principle VIII: Frontend Component Modularity** | Bổ sung nút Sync trực tiếp trên `HomeworkCard`, giao diện gọn gàng, rõ ràng. | **PASS** | Giữ nguyên cấu trúc component sạch sẽ. |
| **Principle IX: Pure Composition** | Không sử dụng base use case trừu tượng. | **PASS** | Giữ các use case độc lập. |

---

## 4. Project Structure

### Documentation (this feature)

```text
specs/013-fix-my-homeworks-coding-submitted/
├── plan.md              # Kế hoạch triển khai (tệp này)
├── research.md          # Phân tích nguyên nhân timeout & so sánh hiệu năng DB vs HTTP
├── data-model.md        # Luồng dữ liệu DB-first cho bài tập và bài nộp
└── quickstart.md        # Hướng dẫn kiểm thử & xác nhận hết lỗi chập chờn
```

### Source Code Impact

```text
backend/app/
└── homework/
    ├── application/
    │   └── get_homeworks_use_case.py       # Thay thế HTTP runtime bằng DB queries
    └── controller.py                       # Cho phép user sync bài của chính mình (Permission READ)

frontend/src/features/homework/
├── components/
│   └── HomeworkCard.tsx                    # Thêm nút bấm 'Đồng bộ kết quả' (Sync)
├── hooks/
│   └── useHomeworks.ts                     # Thêm mutation hook useSyncHomework
└── pages/
    └── MyHomeworkPage.tsx                  # Xử lý trigger sync và refetch
```

---

## 5. Implementation Phases

### Phase 1: Backend - DB-First Submission Retrieval
1. Trong `GetHomeworksUseCase.get_assigned_to_user`:
   - Lấy danh sách submission của `user_id` cho các bài tập trong trang hiện tại: `self.homework_repo.get_submissions_by_user_for_homeworks(homework_ids, user_id)` hoặc lọc qua danh sách submissions của user.
   - Xác định `coding_submitted`: User có ít nhất 1 bài nộp loại CODING (hoặc `is_passed == True`).
   - Xác định `game_submitted`: User có ít nhất 1 bài nộp loại GAME với `is_passed == True`.
   - Tính toán `is_submitted` và `is_overdue` tức thì dựa trên dữ liệu DB.
   - **Xóa bỏ hoàn toàn** đoạn code `tasks.append(fetch_coding)` và `tasks.append(fetch_game)` gọi Quiz API trong luồng này.
2. Tương tự, chuẩn hóa `get_unsubmitted_by_user` và `get_unsubmitted_report` đọc qua DB submissions.

### Phase 2: Backend - Endpoint Sync Cho Học Viên
1. Trong `backend/app/homework/controller.py`:
   - Cập nhật endpoint `POST /{homework_id}/sync`: Cho phép người dùng có quyền `HomeworkPermission.READ` (tức học viên được gán bài) thực hiện đồng bộ bài của chính bài tập đó.

### Phase 3: Frontend - Nút Đồng Bộ Trên HomeworkCard
1. Cập nhật `useSyncHomework` hook trong `frontend/src/features/homework/hooks/useHomeworks.ts`.
2. Trong `HomeworkCard.tsx`:
   - Bổ sung nút **"Đồng bộ kết quả"** (Icon `SyncOutlined`) bên cạnh nút "Chi tiết" / "Làm bài ngay" khi bài tập chưa nộp hoặc đang nộp một phần (`!isSubmitted`).
   - Xử lý trạng thái loading khi đang sync.
   - Sau khi sync xong, tự động gọi query invalidation để cập nhật tức thì trạng thái sang màu xanh lá ("Đã nộp").

### Phase 4: Kiểm thử & Đánh giá
1. Chạy test suite backend: `pytest backend/tests/api/test_homework_api.py -v`.
2. Kiểm tra frontend build: `npm run build` đảm bảo zero typescript errors.
3. Kiểm thử trên browser: Refresh nhiều lần trang `/dashboard/my-homeworks` xác nhận tốc độ tải tức thì và trạng thái không bao giờ bị nhảy thất thường.
