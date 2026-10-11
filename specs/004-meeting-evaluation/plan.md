# Implementation Plan: Đánh Giá Buổi Học (Trainer Đánh Giá Meeting 1-1 & Trainee Đánh Giá Trainer)

**Branch**: `004-meeting-evaluation` | **Date**: 2026-10-11 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/004-meeting-evaluation/spec.md)

**Input**: Feature specification from `/specs/004-meeting-evaluation/spec.md`

## Summary

Xây dựng tính năng Đánh giá Buổi học/Meeting giữa **Trainer (người tạo)** và **Trainee (người tham gia)**:
1. Cho phép Trainer bật cờ `enable_evaluation` khi tạo/sửa buổi học (hạn chót đánh giá mặc định 24h sau khi kết thúc).
2. **Trainer đánh giá tổng thể Buổi học (Quan hệ 1 - 1)**: Trainer chỉ cần gửi 01 phiếu đánh giá tổng thể cho cả buổi học lưu vào bảng riêng `meeting_overall_evaluations` theo 4 tiêu chí chuẩn hóa giữ nguyên (*Chuyên cần & Tác phong*, *Mức độ Tương tác & Đóng góp*, *Mức độ Tiếp thu & Hiểu bài*, *Mức độ Chuẩn bị bài trước buổi học*).
3. **Trainee đánh giá cá nhân Trainer**: Trainee tham gia meeting gửi phản hồi cho Trainer theo 4 tiêu chí giảng dạy (*Chất lượng Nội dung bài học*, *Phương pháp Giảng dạy & Hỗ trợ*, *Không khí Lớp học & Sự tương tác*, *Giá trị Thu nhận & Tính ứng dụng*), hỗ trợ cờ **Ẩn danh** (`is_anonymous`).
4. **Quyền xem kết quả**: Đánh giá tổng thể của Trainer được công khai ngay lập tức cho toàn bộ Trainee tham gia xem.
5. **Cơ chế Vi phạm 24h**: Tác vụ tự động quét sau 24h:
   - Nếu Trainer chưa gửi `MeetingOverallEvaluation` $\rightarrow$ Tự động tạo 01 `Violation`.
   - Nếu Trainee chưa gửi đánh giá Trainer $\rightarrow$ Tự động tạo 01 `Violation`.
6. Cung cấp API tổng hợp thống kê điểm trung bình theo tiêu chí và chi tiết đánh giá.

---

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript / React 18+ (Frontend)

**Primary Dependencies**:
- Backend: FastAPI, SQLAlchemy 2.0, Dishka (Dependency Injection), Pydantic V2, Alembic, APScheduler
- Frontend: React, TanStack Query, TailwindCSS, Lucide Icons, Axios

**Storage**: PostgreSQL (SQLAlchemy models: `meetings`, `meeting_overall_evaluations`, `meeting_evaluations`)

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
| **VI. Idempotency & Network Resilience** | **PASS** | Ngăn chặn đánh giá trùng lặp bằng unique constraint `UNIQUE(meeting_id)` cho overall và `UNIQUE(meeting_id, reviewer_id, target_id)` cho trainee |
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
    └── evaluation-api.json
```

### Source Code (repository root)

```text
backend/app/
├── meeting/
│   ├── domain/
│   │   ├── entity.py                     # Meeting, MeetingOverallEvaluation, MeetingEvaluation
│   │   ├── value_objects.py              # EvaluationScoreItem
│   │   └── events.py                     # MeetingOverallEvaluationSubmittedEvent, TraineeEvaluationSubmittedEvent
│   ├── application/
│   │   ├── __init__.py                   # Re-export all use cases
│   │   ├── submit_meeting_overall_evaluation_use_case.py # Trainer đánh giá meeting 1-1
│   │   ├── get_meeting_overall_evaluation_use_case.py    # Xem đánh giá tổng thể meeting
│   │   ├── submit_trainee_evaluation_use_case.py         # Trainee đánh giá Trainer
│   │   ├── get_meeting_evaluation_summary_use_case.py    # Tổng hợp báo cáo buổi học
│   │   └── check_evaluation_deadline_job_use_case.py     # Quét quá hạn 24h tạo Violation
│   ├── infrastructure/
│   │   ├── model.py                      # MeetingOverallEvaluationModel, MeetingEvaluationModel
│   │   └── repository.py                 # Repository implementation
│   ├── controller.py                     # REST endpoints
│   ├── schemas.py                        # Pydantic Request/Response DTOs
│   └── providers.py                      # Dishka Provider registrations
├── jobs/
│   └── cron_jobs.py                      # Đăng ký job định kỳ kiểm tra hạn 24h đánh giá
└── alembic/versions/                     # Migration script thêm bảng meeting_overall_evaluations và meeting_evaluations

frontend/src/
├── features/
│   └── meeting/
│       ├── components/
│       │   ├── MeetingOverallEvaluationModal.tsx  # Form Trainer đánh giá 1-1 cho buổi học
│       │   ├── TraineeEvaluationModal.tsx         # Form Trainee đánh giá Trainer (có ẩn danh)
│       │   ├── MeetingEvaluationSummaryCard.tsx   # Hiển thị điểm overall & feedback buổi học
│       │   └── StarRatingInput.tsx                # Component chọn điểm 1-5 sao trực quan
│       ├── services/
│       │   └── meetingEvaluationApi.ts            # Axios client endpoints
│       └── types/
│           └── evaluation.types.ts                # TypeScript interfaces
```

**Structure Decision**: Tuân thủ Clean Architecture chuẩn của dự án. Tách riêng nghiệp vụ đánh giá tổng thể buổi học và đánh giá cá nhân Trainer, đồng thời kết nối tự động tạo vi phạm với domain `app/violation`.

---

## Complexity Tracking

*Không có vi phạm Constitution cần giải trình.*
