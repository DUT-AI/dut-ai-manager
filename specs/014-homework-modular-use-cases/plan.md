# Implementation Plan: Tách Biệt Use Case Homework & Dọn Dẹp Code Rác

**Feature**: `014-homework-modular-use-cases`  
**Date**: 2026-10-18  
**Status**: Ready  

## Summary
Refactor monolithic `GetHomeworksUseCase` (chứa 6 method khác nhau) thành 5 Single-Responsibility Use Cases tuân thủ nghiêm ngặt **Nguyên tắc VII (Strict Single-Responsibility Use Cases - One Public Execute Per Class)** trong Constitution v1.5.0. Đồng thời xóa bỏ triệt để các mã nguồn mồ côi/rác (`HomeworkService` rỗng trong `services.py`, `HomeworkGradingService` trong `external_api.py`) và cập nhật toàn bộ call sites (bao gồm module `report`) mà không dùng alias thừa thãi.

---

## Constitution Compliance Check

- [x] **Principle I: Clean Architecture & Practical DDD Boundaries**: Tách Use Case đúng tầng Application; dọn dẹp các service rác.
- [x] **Principle II: Dependency Injection with Dishka**: Đăng ký từng Use Case cụ thể vào `HomeworkModuleProvider` và `ReportModuleProvider`.
- [x] **Principle VII: Strict Single-Responsibility Use Cases**: Mỗi class Use Case chỉ có 1 phương thức công khai `execute(...)`, đặt trong từng file `*_use_case.py`.
- [x] **Principle X: Zero Redundant Backward Compatibility**: Xóa bỏ `GetHomeworksUseCase` cũ sau khi refactor, cập nhật trực tiếp tại mọi nơi gọi (call sites), cấm tạo alias lười biếng.

---

## Phased Implementation Structure

### Phase 1: Tạo 5 Use Case Đơn Nhiệm Mới
1. `backend/app/homework/application/get_homeworks_paged_use_case.py` -> `GetHomeworksPagedUseCase`
2. `backend/app/homework/application/get_homework_detail_use_case.py` -> `GetHomeworkDetailUseCase`
3. `backend/app/homework/application/get_user_homeworks_use_case.py` -> `GetUserHomeworksUseCase`
4. `backend/app/homework/application/get_unsubmitted_homeworks_for_user_use_case.py` -> `GetUnsubmittedHomeworksForUserUseCase`
5. `backend/app/homework/application/get_unsubmitted_homework_report_use_case.py` -> `GetUnsubmittedHomeworkReportUseCase`

### Phase 2: Dọn Dẹp Mã Nguồn Rác & Cập Nhật Export
1. Xóa `backend/app/homework/domain/services.py` (chỉ có pass).
2. Xóa `backend/app/homework/infrastructure/external_api.py` (không nơi nào sử dụng).
3. Cập nhật `backend/app/homework/application/__init__.py` để re-export 5 use case mới và loại bỏ `GetHomeworksUseCase`.
4. Xóa `backend/app/homework/application/get_homeworks_use_case.py`.

### Phase 3: Cập Nhật Dependency Injection & Controllers
1. Cập nhật `backend/app/homework/providers.py` để inject 5 use case mới.
2. Cập nhật `backend/app/homework/controller.py` inject từng Use Case chuyên biệt cho từng endpoint.
3. Cập nhật `backend/app/report/application/use_cases.py` và `backend/app/report/providers.py` để dùng `GetUnsubmittedHomeworksForUserUseCase`.

### Phase 4: Kiểm Thử & Nghiệm Thu
1. Chạy `backend/.venv/bin/pytest backend/tests/api/test_homework_api.py -v`.
2. Chạy test suite toàn diện của backend.
3. Build frontend `npm run build` để đảm bảo hợp chuẩn 100%.
