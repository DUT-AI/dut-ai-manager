# Tasks: Chuẩn Hóa Kiểm Tra Bài Nộp Qua Database & Bổ Sung Nút Sync Thủ Công (My Homeworks)

**Feature**: `013-fix-my-homeworks-coding-submitted`  
**Date**: 2026-10-17  
**Status**: Ready  

---

## Danh Sách Nhiệm Vụ (Task Checklist)

### Phase 1: Backend - DB-First Submissions Retrieval
- [x] **TASK-001**: Trong [repository.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/homework/infrastructure/repository.py), bổ sung phương thức `get_user_submissions_for_homeworks(homework_ids: list[int], user_id: int) -> list[HomeworkSubmissionEntity]` để truy vấn hàng loạt bài nộp của user.
- [x] **TASK-002**: Trong [get_homeworks_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/homework/application/get_homeworks_use_case.py), refactor hàm `get_assigned_to_user` loại bỏ hoàn toàn các cuộc gọi HTTP sang Quiz API (`fetch_coding`, `fetch_game`), thay thế bằng truy vấn từ database nội bộ để tính toán `coding_submitted`, `game_submitted`, `is_submitted` và `is_overdue`.
- [x] **TASK-003**: Cập nhật hàm `get_unsubmitted_by_user` và `get_unsubmitted_report` trong [get_homeworks_use_case.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/homework/application/get_homeworks_use_case.py) để đồng bộ tiêu chí xác định bài nộp theo database.

### Phase 2: Backend - Mở Rộng Quyền Cho Endpoint Sync
- [x] **TASK-004**: Trong [controller.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/homework/controller.py), cập nhật route `POST /{homework_id}/sync` để học viên có quyền `HomeworkPermission.READ` có thể tự kích hoạt đồng bộ bài nộp của chính bài tập đó từ Quiz API về database.

### Phase 3: Frontend - Nút Đồng Bộ Kết Quả Trên Thẻ Bài Tập
- [x] **TASK-005**: Trong [useHomeworks.ts](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/homework/hooks/useHomeworks.ts), cập nhật mutation hook `useSyncHomeworkFromQuiz` tự động làm mới (`invalidateQueries`) query cache của `myHomeworks` (`['homeworks', 'me']`).
- [x] **TASK-006**: Trong [HomeworkCard.tsx](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/homework/components/HomeworkCard.tsx), thêm nút bấm **"Đồng bộ"** (Icon `SyncOutlined`) hiển thị khi bài tập chưa nộp hoặc nộp một phần (`!isSubmitted`), có loading spinner khi đang đồng bộ và thông báo AntD `message.success`.

### Phase 4: Kiểm Thử & Nghiệm Thu
- [x] **TASK-007**: Chạy backend test suite: `pytest backend/tests/api/test_homework_api.py -v` (30/30 passed).
- [x] **TASK-008**: Kiểm tra frontend compile: `npm run build` đảm bảo không phát sinh lỗi TypeScript.
- [x] **TASK-009**: Kiểm tra thực tế trên web browser `http://localhost:5173/dashboard/my-homeworks`: Tốc độ tải tức thì, dữ liệu nhất quán 100%, nút Sync hoạt động mượt mà.
