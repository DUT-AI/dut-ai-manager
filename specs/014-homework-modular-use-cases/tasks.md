# Tasks: Tách Biệt Use Case Homework & Dọn Dẹp Code Rác (014-homework-modular-use-cases)

**Feature**: `014-homework-modular-use-cases`  
**Date**: 2026-10-18  
**Status**: Ready  

---

## Phase 1: Setup & Foundational
**Goal**: Dọn dẹp các tệp/mã nguồn rác và chuẩn bị môi trường cho các Use Case đơn nhiệm.

- [x] T001 [P] Xóa tệp rác `backend/app/homework/domain/services.py` (chứa class rỗng không ai dùng).
- [x] T002 [P] Xóa tệp rác `backend/app/homework/infrastructure/external_api.py` (chứa `HomeworkGradingService` không được sử dụng ở bất kỳ đâu).

---

## Phase 2: User Story 1 - Tách Use Case Truy Vấn Bài Tập (Priority: P1) 🎯 MVP
**Goal**: Tạo 5 Use Case đơn nhiệm độc lập thay thế cho `GetHomeworksUseCase` nguyên khối, mỗi file chỉ có 1 class với 1 method `execute(...)`.

- [x] T003 [P] [US1] Tạo `GetHomeworksPagedUseCase` trong `backend/app/homework/application/get_homeworks_paged_use_case.py` phục vụ phân trang danh sách bài tập.
- [x] T004 [P] [US1] Tạo `GetHomeworkDetailUseCase` trong `backend/app/homework/application/get_homework_detail_use_case.py` phục vụ lấy chi tiết 1 bài tập theo ID.
- [x] T005 [P] [US1] Tạo `GetUserHomeworksUseCase` trong `backend/app/homework/application/get_user_homeworks_use_case.py` phục vụ lấy danh sách bài tập kèm trạng thái nộp bài của học viên.
- [x] T006 [P] [US1] Tạo `GetUnsubmittedHomeworksForUserUseCase` trong `backend/app/homework/application/get_unsubmitted_homeworks_for_user_use_case.py` phục vụ lấy bài tập chưa nộp của 1 user.
- [x] T007 [P] [US1] Tạo `GetUnsubmittedHomeworkReportUseCase` trong `backend/app/homework/application/get_unsubmitted_homework_report_use_case.py` phục vụ thống kê tổng hợp số bài chưa nộp của tất cả user.
- [x] T008 [US1] Cập nhật `backend/app/homework/application/__init__.py` để re-export 5 Use Case mới theo danh sách `__all__` và loại bỏ `GetHomeworksUseCase`.
- [x] T009 [US1] Xóa bỏ tệp nguyên khối cũ `backend/app/homework/application/get_homeworks_use_case.py`.

---

## Phase 3: User Story 3 - Cập Nhật Dependency Injection & Controller (Priority: P2)
**Goal**: Đăng ký các Use Case mới vào Dishka Provider và cập nhật trực tiếp tại router controllers (Homework & Report) mà không dùng alias thừa.

- [x] T010 [US2] Cập nhật Dishka container `backend/app/homework/providers.py` để cung cấp 5 Use Case mới và bỏ provider cũ `get_get_homeworks_use_case`.
- [x] T011 [US2] Cập nhật `backend/app/homework/controller.py` inject trực tiếp các Use Case mới tại từng endpoint (`/`, `/me`, `/{id}`, `/report/unsubmitted`, `/report/unsubmitted/{user_id}`).
- [x] T012 [US2] Cập nhật `backend/app/report/providers.py` và `backend/app/report/application/use_cases.py` để inject `GetUnsubmittedHomeworksForUserUseCase` thay thế cho `GetHomeworksUseCase`.

---

## Phase 4: Polish & Kiểm Thử Toàn Diện
**Goal**: Chạy test suite và build kiểm tra tính tương thích 100%.

- [x] T013 Chạy kiểm thử tự động `backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v` (30/30 passed).
- [x] T014 Chạy kiểm thử tự động cho module report `backend/.venv/bin/pytest backend/tests/api/test_report_api.py -v` (12/12 passed).
- [x] T015 Kiểm tra frontend compile: `npm run build` trong thư mục `frontend` đảm bảo không phát sinh bất kỳ lỗi TypeScript nào.
