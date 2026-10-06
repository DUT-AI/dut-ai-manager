# Implementation Plan: Quản Lý Và Lưu Vết Chi Tiết Lịch Sử Từng Bài Tập Coding

**Branch**: `008-detailed-exercise-history` | **Date**: 2026-10-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/008-detailed-exercise-history/spec.md`

---

## Summary

Tái cấu trúc và nâng cấp cơ chế lưu vết bài tập coding chi tiết giữa **DUT-AI Quiz** và **DUT-AI Manager**:
1. **Quiz**:
   - Cung cấp endpoint `GET /api/v1/lessons/{lesson_slug}/exercises` trả về danh sách các bài tập con của lesson.
   - Nâng cấp Webhook dispatch (`submit_homework_uc.py`) gửi đầy đủ thông tin bài tập con (`exercise_id`, `exercise_title`, `score`, `attempt_number`, `is_passed`...).
   - Sửa logic endpoint `/completed-members` để chỉ đánh dấu hoàn thành khi học viên đã nộp đủ $100\%$ các bài tập coding active.
2. **Manager**:
   - Bổ sung các cột `exercise_id`, `exercise_title`, `score`, `attempt_number` vào bảng `homework_submissions` qua migration Alembic.
   - Định nghĩa các Pydantic Models chuẩn hóa cho Webhook, Sync API và Status API.
   - Nâng cấp `RecordHomeworkSubmissionUseCase` thực hiện idempotent upsert theo `(homework_id, user_id, exercise_id)`.
   - Nâng cấp `GetHomeworkSubmissionStatusUseCase` dựng ma trận tiến độ nộp bài chi tiết ($k/N$ bài tập con).
   - Nâng cấp `CheckOverdueHomeworkUseCase` xác định quá hạn dựa trên việc hoàn thành tất cả bài tập con.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Dishka (DI), Pydantic V2, Alembic, httpx  
**Storage**: PostgreSQL  
**Testing**: pytest, pytest-asyncio  
**Target Platform**: Linux Server / Docker  
**Project Type**: Web Service / Distributed Microservices REST API  
**Performance Goals**: API phản hồi trạng thái nộp bài $< 500\text{ ms}$, xử lý webhook $< 50\text{ ms}$  
**Constraints**: Zero regression, 100% test pass, 0 typecheck diagnostics (`make typecheck`)  
**Scale/Scope**: 2 repositories (`dut-ai-manager` và `dut-ai-quiz`), 1 migration Alembic, ~8 file use cases/dtos/repositories  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- [x] **Zero Hardcoded Secrets**: Sử dụng cấu hình từ `settings.MANAGE_WEBHOOK_SECRET` và `settings.QUIZ_API_URL`.
- [x] **Safe Database Migrations**: Có migration Alembic rõ ràng thêm cột `nullable=True` và index an toàn.
- [x] **Single Responsibility**: Mỗi Use Case là 1 file độc lập trong `app/homework/application/`.
- [x] **Type Safety**: Tất cả DTOs và API Contracts đều dùng Pydantic V2 type annotations chuẩn và vượt qua `make typecheck`.
- [x] **Testing Master**: Cập nhật toàn diện test suite cho Webhook, Sync, Status và Overdue Checker.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-detailed-exercise-history/
├── spec.md              # Feature specification
├── checklists/
│   └── requirements.md  # Quality checklist
├── plan.md              # Implementation plan (this file)
├── research.md          # Technical decisions & rationale
├── data-model.md        # Database schema & entities
├── quickstart.md        # Verification and testing guide
└── contracts/
    ├── webhook_and_sync_contract.md # Webhook & Quiz Sync DTO contracts
    └── manager_status_api.md        # Manager status API response contracts
```

### Source Code Impacted

#### 1. DUT-AI Manager (`/Users/nguyenhuynh/Documents/dut-ai-manager`)
```text
backend/
├── alembic/versions/
│   └── xxxx_add_exercise_details_to_submissions.py
├── app/
│   └── homework/
│       ├── domain/
│       │   └── entity.py                           # Cập nhật HomeworkSubmission entity (exercise_id, score...)
│       ├── infrastructure/
│       │   ├── model.py                            # Cập nhật HomeworkSubmissionModel & index
│       │   ├── repository.py                       # Hỗ trợ upsert & query theo exercise_id
│       │   └── quiz_api.py                         # Bổ sung method get_lesson_exercises
│       └── application/
│           ├── dtos.py                             # Thêm DTOs chi tiết (Exercise, StudentHomeworkDetail...)
│           ├── helpers.py                          # Cập nhật helper kiểm tra hoàn thành tất cả bài con
│           ├── record_submission_use_case.py       # Cập nhật xử lý webhook có exercise_id
│           ├── get_homework_submission_status_use_case.py # Dựng ma trận tiến độ nộp bài k/N
│           └── check_overdue_homework_use_case.py  # Quét quá hạn dựa trên 100% bài con
└── tests/
    ├── test_homework_webhook.py                    # Test webhook nộp từng bài tập con
    └── test_homework/                              # Test status & overdue checker
```

#### 2. DUT-AI Quiz (`/Users/nguyenhuynh/Documents/projects/dut-ai-quiz`)
```text
apps/api/app/
├── presentation/api/routers/
│   ├── lessons.py                                  # Thêm GET /{lesson_slug}/exercises
│   └── homeworks.py                                # Cập nhật /completed-members và /submissions-for-sync
├── application/
│   ├── dtos/homework.py                            # Cập nhật DTOs đồng bộ có exercise_id
│   └── use_cases/homeworks/
│       ├── submit_homework_uc.py                   # Webhook dispatch gửi kèm exercise_id, exercise_title
│       └── list_completed_homework_members_uc.py   # Check điều kiện nộp đủ 100% bài tập con
└── infrastructure/
    ├── repositories/homeworks.py                   # Cập nhật SQL query count distinct homeworks
    └── services/manage_webhook.py                  # Mở rộng tham số dispatch webhook
```

---

## Complexity Tracking

| Thành phần | Tại sao cần thiết | Giải pháp thay thế đơn giản hơn bị từ chối vì |
| :--- | :--- | :--- |
| **Lưu `exercise_id` trong `homework_submissions`** | Cần lưu vết chính xác học viên đã nộp bài tập coding con nào | Nếu không lưu `exercise_id`, Manager chỉ biết có nộp bài chung chung và bị lừa khi học viên nộp 1 bài rồi bỏ các bài khác |
| **Pydantic Validation 2 chiều** | Đảm bảo tính toàn vẹn kiểu dữ liệu giữa 2 service độc lập | Nếu dùng `dict` tự do không validate sẽ dễ gây runtime crash khi một bên thay đổi định dạng |
