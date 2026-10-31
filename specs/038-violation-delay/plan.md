# Implementation Plan: Lùi thời điểm quét vi phạm thêm 2 ngày (038-violation-delay)

**Branch**: `038-violation-delay` | **Date**: 2026-10-31 | **Spec**: [specs/038-violation-delay/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/038-violation-delay/spec.md)

**Input**: Feature specification from `specs/038-violation-delay/spec.md`

## Summary

Nâng cấp 4 background jobs và use cases kiểm tra vi phạm với quy tắc then chốt:
- **Thời điểm chạy job quét**: Chạy lùi 2 ngày (`target_date = today - 2 ngày` khi chạy tự động theo lịch cron), giúp hệ thống có độ trễ đối soát dữ liệu và đơn phép.
- **Quy tắc phạt trễ**: **TUYỆT ĐỐI KHÔNG GIA HẠN NỘP BÀI HAY HOÀN THÀNH TRỄ**. Mọi task nộp sau deadline ban đầu hoặc chưa nộp trước deadline đều bị tính là vi phạm và tạo violation khi job quét.
- Cụ thể:
  1. `CheckOverdueHomeworkUseCase`: Tự động quét bài tập hạn `today - 2 ngày`. Kiểm tra nghiêm ngặt `submitted_at <= deadline`, nộp sau deadline vẫn bị phạt.
  2. `CheckMeetingAttendanceUseCase`: Tự động quét cuộc họp ngày `today - 2 ngày`.
  3. `CheckOverdueDutiesUseCase`: Tự động quét ca trực nhật ngày `today - 2 ngày` (hạn chốt 22:00 ngày trực).
  4. `CheckEvaluationDeadlineJobUseCase`: Chạy quét các buổi học kết thúc quá 72h (`now - timedelta(hours=72)`).

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Dishka (DI), APScheduler, SQLAlchemy 2.0, Pydantic V2, Loguru  
**Storage**: PostgreSQL (TimescaleDB / SQLAlchemy ORM), không cần thay đổi schema hay migration  
**Testing**: `pytest`, `pytest-asyncio` (`backend/.venv/bin/pytest`)  
**Target Platform**: Linux Server / Docker container (Backend Service)  
**Project Type**: Web Service / Background Job Scheduler  
**Performance Goals**: Không phát sinh overhead query  
**Constraints**: 
- Bảo toàn nguyên vẹn ngày giờ deadline hiển thị trên giao diện người dùng và cơ sở dữ liệu.
- Mốc deadline ban đầu là mốc cut-off duy nhất để xác định bài nộp hợp lệ hay trễ.
- Khi truyền tham số `target_date` vào Use Case, hệ thống sử dụng chính xác ngày đó.  
**Scale/Scope**: 4 background jobs, 4 use case classes, các file constants tương ứng, và unit tests.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú tuân thủ |
|---|---|---|
| **I. Clean Architecture & Practical DDD Boundaries** | **PASS** | Hằng số cấu hình nằm trong Domain layer (`constants.py`). Use cases tại Application layer xử lý logic điều phối. |
| **II. Dependency Injection with Dishka** | **PASS** | Sử dụng toàn bộ container Dishka hiện có, không can thiệp khởi tạo ad-hoc. |
| **III. Enterprise UTC Storage & Vietnam Display Integrity** | **PASS** | Tính toán ngày hiệu lực từ UTC chuyển sang `Asia/Ho_Chi_Minh` (`target_date = now_vn.date() - timedelta(days=2)`). So sánh thời gian đánh giá bằng UTC timezone-aware. |
| **IV. Event-Driven Decoupling** | **PASS** | Tiếp tục phát tán các Domain Events (`HomeworkOverdueDetected`, `ParticipantAbsenceRecorded`, `ParticipantLateRecorded`, `DutyViolated`) qua `EventBus`. |
| **V. API Backward Compatibility** | **PASS** | Không sửa đổi bất kỳ contract API public nào. |
| **VII. Strict Single-Responsibility Use Cases** | **PASS** | Giữ nguyên mỗi use case một trách nhiệm. |
| **IX. Pure Composition Over Base Use Cases** | **PASS** | Sử dụng composition và domain constants. |
| **X. Zero Redundant Backward Compatibility** | **PASS** | Cập nhật trực tiếp hằng số và chuỗi lý do vi phạm. |

*Kết quả GATE: PASS (Không có vi phạm hiến pháp).*

---

## Project Structure

### Documentation (this feature)

```text
specs/038-violation-delay/
├── plan.md              # Kế hoạch thực hiện tổng thể (artifact này)
├── research.md          # Quyết định kỹ thuật & thiết kế (Phase 0)
├── data-model.md        # Mô hình dữ liệu & dòng trạng thái thời gian (Phase 1)
├── contracts/           
│   └── job-contracts.md # Đặc tả giao diện các Jobs và Use Cases (Phase 1)
├── quickstart.md        # Hướng dẫn chạy & kiểm thử nghiệm thu (Phase 1)
└── tasks.md             # Danh sách task chi tiết (Phase 2 - speckit-tasks)
```

### Source Code (repository root)

```text
backend/app/
├── violation/
│   └── domain/
│       └── constants.py                                # DEFAULT_VIOLATION_CHECK_DELAY_DAYS = 2
├── homework/
│   ├── domain/
│   │   └── constants.py                                # HOMEWORK_VIOLATION_CHECK_DELAY_DAYS = 2
│   └── application/
│       └── check_overdue_homework_use_case.py          # default target_date = today - delay, check submitted_at <= deadline
├── meeting/
│   ├── domain/
│   │   └── constants.py                                # MEETING_ATTENDANCE_CHECK_DELAY_DAYS = 2, EVALUATION_DEADLINE_HOURS = 72
│   └── application/
│       ├── check_meeting_attendance_use_case.py        # default target_date = today - delay
│       └── check_evaluation_deadline_job_use_case.py   # end_bound = now - 72h, start_bound = now - 9d
├── duty/
│   ├── domain/
│   │   └── constants.py                                # DUTY_VIOLATION_CHECK_DELAY_DAYS = 2
│   └── application/
│       └── check_overdue_duties_use_case.py            # default target_date = today - delay
└── tests/
    └── unit/
        ├── test_homework_checker.py                    # Cập nhật & bổ sung test delay 2 ngày & late submission
        ├── test_meeting_use_cases.py                   # Cập nhật & bổ sung test delay 2 ngày
        ├── test_duty_use_cases.py                      # Cập nhật & bổ sung test delay 2 ngày
        └── test_meeting_evaluation.py                  # Cập nhật & bổ sung test 72h deadline
```

---

## Complexity Tracking

> Không có vi phạm Hiến pháp cần biện minh.
