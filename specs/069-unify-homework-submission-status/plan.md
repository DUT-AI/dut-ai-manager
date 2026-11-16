# Implementation Plan: Đồng bộ và Thống nhất Trạng thái Hoàn thành Bài tập giữa Học viên và Quản lý

**Branch**: `069-unify-homework-submission-status` | **Date**: 2026-11-15 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/069-unify-homework-submission-status/spec.md`

---

## Summary

Khắc phục triệt để sự mâu thuẫn trạng thái nộp bài giữa Giao diện Học viên (`MyHomeworkPage`) và Giao diện Quản lý (`HomeworkDetailPage`). Chuẩn hóa cơ chế tính toán nộp bài tại Aggregate Root `Homework.evaluate_submissions` để kiểm tra nghiêm ngặt danh sách bài tập coding con yêu cầu (`total_coding_required`), chuyển đổi học sinh mới làm dở một phần ($K/N$ bài) sang trạng thái `PARTIALLY_SUBMITTED` (`is_submitted = False`). Cung cấp các trường tiến độ chi tiết qua DTO `HomeworkResponse` và cập nhật các thành phần giao diện Frontend (`HomeworkCard`, `MyHomeworkPage`) hiển thị trực quan trạng thái làm dở (Badge Warning/Amber, tiến độ $K/N$), đảm bảo thống nhất 100% dữ liệu trên toàn hệ thống.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend), TypeScript 5.x / React 19 (Frontend)  
**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0, Dishka (DI Container), Pydantic V2, httpx
- Frontend: React 19, Vite, Ant Design (AntD v5), TanStack Query (React Query v5), Tailwind CSS v4, motion/react  
**Storage**: PostgreSQL 16 (Bảng `homeworks`, `homework_assignees`, `homework_submissions`)  
**Testing**: pytest (unit & integration tests), vitest  
**Target Platform**: Web application (Responsive desktop & mobile, PWA)  
**Project Type**: Full-stack web application  
**Performance Goals**: API response time < 200ms p95 cho phân trang 20 bài tập trên `my-homeworks`  
**Constraints**:
- Không thêm các cuộc gọi HTTP ra bên ngoài lặp lại trên danh sách phân trang (dùng truy vấn SQL gom nhóm `exercise_id`s tối ưu).
- Tuân thủ nghiêm ngặt Hiến pháp dự án (Constitution): Clean Architecture, Single-Responsibility Use Cases, Non-Null Contract DTOs, Không dùng Fake Optionals.  
**Scale/Scope**: Áp dụng cho toàn bộ học viên và bài tập trên hệ thống DUT AI Manager.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Clean Architecture & Practical DDD Boundaries (MUST)**: Logic đánh giá nằm tại Aggregate Root `Homework` và Value Object `SubmissionEvaluation`. Các use case đóng vai trò điều phối mỏng. Truy vấn dữ liệu thực hiện qua Repository.
- [x] **II. Dependency Injection with Dishka (MUST)**: Mọi use case, repository và service đều đăng ký trong Dishka providers và inject qua `@inject`.
- [x] **III. Enterprise UTC Storage & Vietnam Display Integrity (MUST)**: Tất cả so sánh deadline và timestamp nộp bài đều sử dụng timezone-aware UTC (`ensure_utc`).
- [x] **V. API Backward Compatibility & Non-Null Contract DTOs (MUST)**: `HomeworkResponse` bổ sung các trường tiến độ mới với giá trị mặc định an toàn, không phá vỡ cấu trúc JSON trả về cho mobile/web.
- [x] **VII. Strict Single-Responsibility Use Cases (MUST)**: Giữ nguyên cấu trúc mỗi use case trong một file riêng (`get_user_homeworks_use_case.py`, `get_unsubmitted_homeworks_for_user_use_case.py`, etc.).
- [x] **VIII. Frontend Component Modularity & Single-Responsibility UI (MUST)**: Logic hiển thị thẻ bài tập nằm riêng trong `HomeworkCard.tsx`, trang `MyHomeworkPage.tsx` đóng vai trò điều phối và phân loại tab.
- [x] **IX. Pure Composition & Domain Services Over Base Use Cases (MUST)**: Không dùng Base Use Case; sử dụng phương thức của Aggregate Root `Homework` và repository methods cho việc tổng hợp dữ liệu.
- [x] **X. Zero Redundant Backward Compatibility & Contextual Field Ownership (MUST)**: Chuẩn hóa logic đánh giá thành Single Source of Truth duy nhất, không tạo cờ tạm thời hay hàm bí danh trùng lặp.
- [x] **XIV. No Fake Optionals & Fail-Fast Parameter Contracts (MUST)**: Các trường DTO và tham số được định kiểu tường minh, không dùng fallback giả.

---

## Project Structure

### Documentation (this feature)

```text
specs/069-unify-homework-submission-status/
├── plan.md              # Kế hoạch thực thi tổng thể
├── research.md          # Nghiên cứu giải pháp kỹ thuật (Phase 0)
├── data-model.md        # Cấu trúc thực thể, Value Objects, DTOs (Phase 1)
├── quickstart.md        # Hướng dẫn kiểm thử & xác thực end-to-end (Phase 1)
├── contracts/           # API contracts và giao diện (Phase 1)
│   └── api_contract.md
└── tasks.md             # Danh sách nhiệm vụ chi tiết (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── homework/
│   │   ├── domain/
│   │   │   ├── entity.py                  # Mở rộng evaluate_submissions với required_exercise_ids
│   │   │   └── value_objects.py           # Bổ sung coding_status, total_coding_required/completed vào SubmissionEvaluation
│   │   ├── application/
│   │   │   ├── dtos.py                    # Cập nhật HomeworkResponse với các trường tiến độ mới
│   │   │   ├── get_user_homeworks_use_case.py            # Truy vấn required_exercise_ids và đánh giá chính xác
│   │   │   ├── get_unsubmitted_homeworks_for_user_use_case.py  # Đưa bài làm dở vào danh sách chưa nộp
│   │   │   └── get_unsubmitted_homework_report_use_case.py     # Tính bài làm dở vào báo cáo chưa nộp
│   │   └── infrastructure/
│   │       └── homework_submission_repository.py         # Thêm get_required_exercise_ids_map(homework_ids)
│   └── reminder/
│       └── application/
│           └── scanners/
│               └── homework_scanner.py    # Quét nhắc nhở cho cả bài tập đang làm dở
└── tests/
    └── unit/
        ├── test_homework_validation.py    # Test logic evaluate_submissions với bài làm dở
        └── test_get_user_homeworks.py     # Test use case trả về đúng trạng thái PARTIALLY_SUBMITTED

frontend/
├── src/
│   └── features/
│       └── homework/
│           ├── types/
│           │   └── homework.types.ts      # Bổ sung coding_status, total_coding_required/completed vào Homework interface
│           ├── components/
│           │   └── HomeworkCard.tsx       # Hiển thị trạng thái Amber/Warning khi isPartial kèm tiến độ K/N
│           └── pages/
│               └── MyHomeworkPage.tsx     # Phân loại tab Chưa nộp (gồm làm dở) và Đã nộp (chỉ 100%)
```

**Structure Decision**:
Dự án là ứng dụng Web Full-Stack theo Clean Architecture. Toàn bộ thay đổi tập trung vào domain `homework` ở backend và feature `homework` ở frontend, đảm bảo tuân thủ tuyệt đối cấu trúc thư mục hiện có.

---

## Complexity Tracking

> Không có vi phạm Hiến pháp (No Constitution Violations). Mọi giải pháp tuân thủ hoàn toàn quy chuẩn Clean Architecture và Single Source of Truth.
