# Implementation Plan: Chuẩn Hóa Thời Gian Xảy Ra Vi Phạm Tự Động Theo UTC

**Branch**: `068-violation-occurrence-date-utc` | **Date**: 2026-11-13 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/068-violation-occurrence-date-utc/spec.md)

**Input**: Feature specification from `/specs/068-violation-occurrence-date-utc/spec.md`

## Summary

Chuyển đổi toàn bộ các tác vụ định kỳ (background jobs) và event handlers tạo vi phạm tự động sang việc ghi nhận thời gian vi phạm (`date`) theo đúng thời điểm xảy ra sự việc vi phạm (occurrence timestamp) dưới định dạng timezone-aware UTC, thay vì lấy thời điểm chạy job (`datetime.now(UTC)`). Đảm bảo frontend hiển thị chính xác giờ vi phạm theo múi giờ địa phương của client (`Asia/Ho_Chi_Minh` hoặc múi giờ trình duyệt).

## Technical Context

**Language/Version**: Python 3.12+, TypeScript / React 19  
**Primary Dependencies**: FastAPI, Pydantic V2, SQLAlchemy 2.0, APScheduler, Dishka, Dayjs  
**Storage**: PostgreSQL with `TIMESTAMPTZ` (`DateTime(timezone=True)`)  
**Testing**: pytest (backend), npm run build / vitest (frontend)  
**Target Platform**: Linux Server / Docker, Web (Desktop & Mobile)  
**Project Type**: Web Service (Backend + Frontend)  
**Performance Goals**: Không tăng thời gian thực thi của scheduler hay event handlers, truy vấn theo date range vẫn tối ưu với index `date`.  
**Constraints**: Tuân thủ nghiêm ngặt Principle III (Enterprise UTC Storage) và Principle IV (Event-Driven Decoupling) của Constitution.  
**Scale/Scope**: Bao phủ 5 loại vi phạm tự động: Vắng họp, Đi trễ họp, Quá hạn nộp bài tập, Quá hạn trực nhật, và Quá hạn đánh giá 24h.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I (Clean Architecture & Practical DDD Boundaries)**: Logic nghiệp vụ xác định thời điểm xảy ra vi phạm nằm trong Domain / Application Use Cases. Entities và Events độc lập, không phụ thuộc framework.
- [x] **Principle II (Dependency Injection with Dishka)**: Tất cả use cases và handlers tiếp tục được phân giải qua Dishka containers.
- [x] **Principle III (Enterprise UTC Storage & Vietnam Display Integrity)**: Tất cả mốc thời gian vi phạm (`date`) được chuẩn hóa timezone-aware UTC (`timezone.utc` / `UTC`), không dùng naive datetime.
- [x] **Principle IV (Event-Driven Decoupling)**: Sự kiện điểm danh và bài tập tiếp tục phát tán qua `EventBus`, truyền thêm timestamp sự kiện trong DomainEvent.
- [x] **Principle VII (Strict Single-Responsibility Use Cases)**: Giữ nguyên cấu trúc use case đơn mục tiêu, chỉ cập nhật tham số truyền vào `create_violation_use_case.execute` và domain events.
- [x] **Principle X (Zero Redundant Backward Compatibility)**: Cập nhật trực tiếp các call site của Domain Events và Use Cases, không tạo hàm wrapper dư thừa.

## Project Structure

### Documentation (this feature)

```text
specs/068-violation-occurrence-date-utc/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 contracts
```

### Source Code

```text
backend/
├── app/
│   ├── core/
│   │   └── scheduler.py
│   ├── shared/
│   │   └── domain/
│   │       └── datetime_types.py
│   ├── meeting/
│   │   ├── application/
│   │   │   ├── check_meeting_attendance_use_case.py
│   │   │   └── check_evaluation_deadline_job_use_case.py
│   │   └── domain/
│   │       └── events.py
│   ├── homework/
│   │   ├── application/
│   │   │   └── check_overdue_homework_use_case.py
│   │   └── domain/
│   │       └── value_objects.py
│   ├── duty/
│   │   └── application/
│   │       └── check_overdue_duties_use_case.py
│   └── violation/
│       ├── application/
│       │   ├── create_violation_use_case.py
│       │   └── event_handlers.py
│       ├── domain/
│       │   └── entity.py
│       └── infrastructure/
│           ├── model.py
│           └── repository.py

frontend/
└── src/
    └── features/
        └── violations/
            └── components/
                └── ViolationTable.tsx
```

## Implementation Phases

### Phase 0: Outline & Research
- Nghiên cứu cơ chế chuyển đổi múi giờ chuẩn trong dự án (`to_utc_datetime` hoặc `.astimezone(UTC)`).
- Xác định điểm dữ liệu thời gian chính xác cho từng loại vi phạm:
  1. Vắng sinh hoạt: `meeting.start_time` (chuyển sang UTC nếu là naive).
  2. Đi trễ sinh hoạt: `event.check_in_at` (thời điểm quẹt thẻ check-in thực tế).
  3. Quá hạn bài tập: `assignment.deadline` (thời hạn cụ thể của học viên, UTC).
  4. Quá hạn trực nhật: `meeting.end_time` (nếu ca trực có meeting) hoặc 23:59:59 của `duty_date` theo giờ VN chuyển UTC.
  5. Quá hạn đánh giá 24h: `meeting.end_time + 24 hours` (thời điểm hết hạn đánh giá, UTC).
- Đánh giá tác động đến hàm chống trùng lặp `ViolationRepository.get_by_user_and_date` và `ViolationRepository.exists_by_user_and_reason`.

### Phase 1: Design & Contracts
- Cập nhật định nghĩa Domain Events (`ParticipantAbsenceRecorded`, `HomeworkOverdueDetected`).
- Thiết kế đặc tả hợp đồng dữ liệu cho `Violation` entity và DTO.
- Xây dựng tài liệu kiểm thử và hướng dẫn kích hoạt (quickstart).
