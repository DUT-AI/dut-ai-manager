# Implementation Plan: Đánh Giá 2 Chiều Buổi Học / Meeting (Trainer & Trainee)

**Branch**: `004-meeting-evaluation` | **Date**: 2026-10-02 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/004-meeting-evaluation/spec.md)

**Input**: Feature specification from `/specs/004-meeting-evaluation/spec.md`

## Summary

Xây dựng tính năng Đánh giá 2 chiều cho Buổi học/Meeting giữa **Trainer (người tạo)** và **Trainee (người tham gia)**:
1. Cho phép Trainer bật cờ `enable_evaluation` khi tạo/sửa buổi học (hạn chót đánh giá mặc định 24h sau khi kết thúc).
2. Định nghĩa Bộ 4 tiêu chí chuẩn hệ thống (System Defaults):
   - Trainer đánh giá Trainee: *Chuyên cần & Tác phong*, *Mức độ Tương tác & Đóng góp*, *Mức độ Tiếp thu & Hiểu bài*, *Mức độ Chuẩn bị bài trước buổi học*.
   - Trainee đánh giá Buổi học/Trainer: *Chất lượng Nội dung bài học*, *Phương pháp Giảng dạy & Hỗ trợ*, *Không khí Lớp học & Sự tương tác*, *Giá trị Thu nhận & Tính ứng dụng*.
3. Hỗ trợ tùy chọn gửi đánh giá **Ẩn danh** cho Trainee.
4. Tự động quét sau 24h buổi học kết thúc: Nếu Trainer hoặc Trainee chưa hoàn thành đánh giá thì tự động tạo 01 bản ghi `Violation` (Vi phạm) và tạm khóa quyền xem chi tiết đánh giá chéo.
5. Cung cấp API tổng hợp thống kê điểm trung bình theo tiêu chí, xem lịch sử nhận xét và tiến độ đánh giá.

---

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript / React 18+ (Frontend)

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0, Dishka (Dependency Injection), Pydantic V2, Alembic, APScheduler (hoặc async cron jobs)
- Frontend: React, TanStack Query, TailwindCSS, Lucide Icons, Axios

**Storage**: PostgreSQL (SQLAlchemy models: `meetings`, `meeting_evaluations`, `evaluation_criteria`)

**Testing**: Pytest (Unit tests cho domain/use cases, Integration tests cho repositories/controllers)

**Target Platform**: Web Application (Backend REST API + Frontend SPA)

**Project Type**: Web Service / Fullstack Application

**Performance Goals**: API response time < 200ms cho việc nộp đánh giá và lấy báo cáo thống kê

**Constraints**:
- Tuân thủ nghiêm ngặt DUT AI Manager Constitution: Clean Architecture / DDD, Dishka DI, Timezone UTC+7, 1 File / 1 Use Case.
- Zero breaking changes đối với schema và API hiện tại của domain `Meeting` và `Violation`.
- Đảm bảo tính toàn vẹn và ẩn danh tuyệt đối khi `is_anonymous = true`.

**Scale/Scope**: ~100 buổi học/tháng, 1000 học viên, hàng nghìn phiếu đánh giá.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú tuân thủ |
|---|:---:|---|
| **I. Clean Architecture & DDD Boundaries** | **PASS** | Tách bạch rõ `domain/`, `application/`, `infrastructure/`, `controller.py`, `schemas.py` |
| **II. Dependency Injection with Dishka** | **PASS** | Đăng ký toàn bộ use cases và repositories mới vào `providers.py` của domain `Meeting` |
| **III. Unified UTC+7 Timezone** | **PASS** | Sử dụng `get_current_utc7_time()` cho mọi mốc deadline 24h và thời gian gửi đánh giá |
| **IV. Event-Driven Decoupling** | **PASS** | Bắn Domain Event khi hoàn tất đánh giá hoặc kích hoạt vi phạm 24h qua EventBus / Job |
| **V. API Backward Compatibility & Envelope** | **PASS** | Kế thừa router hiện tại, trả về `ApiResponse[T]` chuẩn hóa |
| **VI. Idempotency & Network Resilience** | **PASS** | Ngăn chặn đánh giá trùng lặp bằng unique constraints `(meeting_id, reviewer_id, target_id)` |
| **VII. Single-Responsibility Use Cases** | **PASS** | Mỗi use case đặt trong 1 file `*_use_case.py` riêng và export qua `__all__` tại `__init__.py` |

---

## Project Structure

### Documentation (this feature)

```text
specs/004-meeting-evaluation/
├── spec.md              # Feature specification
├── plan.md              # This implementation plan
├── research.md          # Technical choices and research decisions
├── data-model.md        # Database schemas and domain entity models
├── quickstart.md        # Run and test guide
└── contracts/           # API contract schemas (OpenAPI / JSON schemas)
    ├── evaluation-api.json
    └── criteria-api.json
```

### Source Code (repository root)

```text
backend/app/
├── meeting/
│   ├── domain/
│   │   ├── entity.py                     # Cập nhật Meeting, thêm MeetingEvaluation, EvaluationCriteria
│   │   ├── value_objects.py              # EvaluationType, EvaluationTargetType, EvaluationStatus
│   │   └── events.py                     # EvaluationSubmittedEvent, EvaluationOverdueEvent
│   ├── application/
│   │   ├── __init__.py                   # Re-export all use cases
│   │   ├── submit_trainer_evaluation_use_case.py
│   │   ├── submit_trainee_evaluation_use_case.py
│   │   ├── get_meeting_evaluation_summary_use_case.py
│   │   ├── get_my_evaluation_result_use_case.py
│   │   ├── get_evaluation_criteria_use_case.py
│   │   └── check_evaluation_deadline_job_use_case.py
│   ├── infrastructure/
│   │   ├── model.py                      # SQLAlchemy models: MeetingEvaluationModel, EvaluationCriteriaModel
│   │   └── repository.py                 # MeetingEvaluationRepository implementation
│   ├── controller.py                     # REST endpoints cho evaluation
│   ├── schemas.py                        # Pydantic Request/Response DTOs
│   └── providers.py                      # Dishka Provider registrations
├── jobs/
│   └── cron_jobs.py                      # Đăng ký job định kỳ kiểm tra hạn 24h đánh giá
└── alembic/versions/                     # Migration script thêm bảng và cột mới

frontend/src/
├── features/
│   └── meeting/
│       ├── components/
│       │   ├── MeetingEvaluationFormModal.tsx     # Form đánh giá dành cho Trainer & Trainee
│       │   ├── MeetingEvaluationSummaryCard.tsx    # Báo cáo tổng hợp điểm & phân tích tiêu chí
│       │   └── StarRatingInput.tsx                # Component chọn điểm 1-5 sao trực quan
│       ├── services/
│       │   └── meetingEvaluationApi.ts            # Axios client endpoints
│       └── types/
│           └── evaluation.types.ts                # TypeScript interfaces
```

**Structure Decision**: Web application theo chuẩn Clean Architecture hiện tại của dự án. Mở rộng trực tiếp trong domain `app/meeting` kết hợp liên kết tạo vi phạm sang domain `app/violation`.

---

## Complexity Tracking

*Không có vi phạm Constitution cần giải trình.*
