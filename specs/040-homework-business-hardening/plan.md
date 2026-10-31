# Implementation Plan: Homework Business Hardening

**Branch**: `040-homework-business-hardening` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/040-homework-business-hardening/spec.md`

## Summary

Củng cố toàn diện nghiệp vụ và tính toàn vẹn dữ liệu cho domain Bài tập (Homework):
1. Khắc phục logic nhắc nhở của `HomeworkTaskScanner`: Đánh giá trạng thái nộp bài toàn diện qua `hw.evaluate_submissions()` thay vì chỉ kiểm tra sự tồn tại của mảng `submissions`.
2. Chuẩn hóa danh mục bài tập con qua `QuizApiClient.get_lesson_exercises(slug)` trong `CheckOverdueHomeworkUseCase` và `GetHomeworkSubmissionStatusUseCase`, loại bỏ việc suy đoán mò mẫm từ database cũ, kèm cơ chế fallback an toàn khi mất mạng.
3. Củng cố rào chắn chống gian lận trong `PostponeStrategy.validate()`: Chặn ngày gia hạn trong quá khứ, chặn bài tập đã quá hạn, chặn bài tập đã làm xong; đồng thời cho phép hoãn tích luỹ nhiều lần nối tiếp (mỗi lần <= 4 ngày so với deadline hiện tại).

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Pydantic V2, SQLAlchemy 2.0, Dishka DI, httpx, loguru  
**Storage**: PostgreSQL (TimescaleDB / UTC Timestamps), SQLAlchemy ORM  
**Testing**: pytest (pytest-asyncio)  
**Target Platform**: Linux Server / Docker Container / macOS dev  
**Project Type**: Web Service API & Background Workers (FastAPI Backend)  
**Performance Goals**: Quét nhắc nhở và kiểm tra bài tập < 1.0 giây, phản hồi API < 100ms  
**Constraints**: Tuân thủ triệt để Hiến pháp dự án `v1.9.0` (Fail-Fast, Single Source of Truth, Enterprise UTC, No Fake Optionals)  
**Scale/Scope**: ~100 học viên, hàng nghìn lượt nộp bài, hàng trăm bài tập  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Justification / Notes |
|---|---|---|
| I. Clean Architecture & DDD | PASS | Tách bạch Domain Entities (`Homework.evaluate_submissions`), Use Cases (`check_overdue`, `get_submission_status`), Strategies (`PostponeStrategy`), và Infra (`QuizApiClient`, `HomeworkAssigneeRepository`). |
| II. Dependency Injection (Dishka) | PASS | Toàn bộ dependencies mới (`quiz_api` cho `CheckOverdueHomeworkUseCase`, `homework_submission_repo` cho `PostponeStrategy`) được đăng ký và resolve qua Dishka providers (`providers.py`). |
| III. Enterprise UTC Storage | PASS | Mọi phép so sánh thời gian (`extended_deadline`, `current_deadline`, `now_utc`) đều được chuẩn hóa qua `ensure_utc()` và `datetime.now(UTC)`. |
| VII. Single-Responsibility Use Cases | PASS | Mỗi use case giữ nguyên 1 file riêng biệt và 1 method `execute()`. |
| X. Zero Redundant Compatibility & Contextual Field Ownership | PASS | `assignee.deadline` là nguồn chân lý duy nhất. Không hồi sinh cột deadline cũ trên bảng `homeworks`. |
| XIII. Structured Generic Payload | PASS | Dữ liệu đơn hoãn tiếp tục sử dụng `PostponePayload` với Pydantic type safety. |
| XIV. No Fake Optionals & Fail-Fast Contracts | PASS | Tất cả dependencies trong constructor và helper methods là non-nullable (`Type`, không dùng `Type \| None = None`). Kiểm tra rào chắn ném lỗi `HTTPException 400` rõ ràng, không fallback giá trị giả. |

## Project Structure

### Documentation (this feature)

```text
specs/040-homework-business-hardening/
├── plan.md              # Kế hoạch kiến trúc và thiết kế kỹ thuật
├── research.md          # Phân tích kỹ thuật và quyết định kiến trúc
├── data-model.md        # Mô hình thực thể và quy tắc nghiệp vụ
├── quickstart.md        # Hướng dẫn xác minh và kịch bản test tự động
├── contracts/           # Đặc tả giao diện tích hợp Quiz API & Endpoints
│   └── quiz-exercises-api.md
└── checklists/
    └── requirements.md  # Bảng kiểm tra chất lượng đặc tả
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── homework/
│   │   ├── application/
│   │   │   ├── check_overdue_homework_use_case.py       # Tích hợp quiz_api.get_lesson_exercises
│   │   │   └── get_homework_submission_status_use_case.py # Hiển thị bài con từ Quiz API
│   │   └── providers.py                                # Dishka injection cho check_overdue
│   ├── permission_request/
│   │   ├── application/
│   │   │   └── strategies/
│   │   │       └── postpone_strategy.py                 # Rào chắn chống gian lận & hoãn tích luỹ
│   │   └── providers.py                                # Inject homework_submission_repo
│   └── reminder/
│       └── application/
│           └── scanners/
│               └── homework_scanner.py                 # Đánh giá toàn diện qua evaluate_submissions
└── tests/
    └── unit/
        ├── test_homework_checker.py                    # Unit tests kiểm tra bài con từ Quiz
        ├── test_permission_strategies.py               # Unit tests rào chắn đơn hoãn
        └── test_reminder_use_cases.py                  # Unit tests nhắc nhở đầy đủ Coding + Game
```

**Structure Decision**: Giữ nguyên kiến trúc module hóa hiện tại của backend. Không tạo thêm layer trung gian dư thừa.

## Complexity Tracking

*No violations detected. Zero unnecessary complexity.*
