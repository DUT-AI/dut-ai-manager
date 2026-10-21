# Implementation Plan: Nhắc Nhở Buổi Họp / Lịch Sinh Hoạt Sắp Diễn Ra Cho Thành Viên (Upcoming Meeting Attendance Reminder)

**Branch**: `023-upcoming-meeting-reminder` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/023-upcoming-meeting-reminder/spec.md`

## Summary

Triển khai tính năng tự động quét và nhắc nhở thành viên chuẩn bị tham gia buổi họp / sinh hoạt sắp diễn ra qua cơ chế đa kênh (Web In-App, Discord DM, Web Push PWA):
- Bổ sung `UpcomingMeetingTaskScanner` theo chuẩn `BaseTaskScanner` (Strategy Pattern) để quét các buổi họp sắp tới trong vòng 48h.
- Tự động áp dụng chiến lược Hybrid: 4 mốc đếm ngược (`OFFSET_1D`, `OFFSET_12H`, `OFFSET_4H`, `OFFSET_1H`) kết hợp 4 khung giờ cố định trong ngày (`08:00`, `12:00`, `19:30`, `22:00` UTC+7).
- Lọc chính xác trạng thái người tham gia: Tự động loại trừ người đã được duyệt vắng có phép (`ABSENT_EXCUSED`), người đã chuyển ca, hoặc người đã hoàn thành/điểm danh (`JOINED`, `COMPLETED`).
- Mở rộng `TaskType.MEETING`, tích hợp liền mạch vào `ScanAndSendRemindersUseCase` qua Dishka DI Container mà không làm thay đổi hay làm phình to Use Case cốt lõi.
- Gửi thông báo trực tiếp qua `ReminderDispatcher` và hiển thị đồng bộ trên trang Quản lý Thông báo `/dashboard/notifications` thuộc danh mục Cuộc họp (`MEETING`).

## Technical Context

- **Language/Version**: Python 3.12 (Backend) + TypeScript / React 18 (Frontend)
- **Primary Dependencies**: FastAPI, Dishka (Dependency Injection), SQLAlchemy 2.0 (ORM), Pydantic v2
- **Storage**: PostgreSQL (`notifications` table) - Tái sử dụng bảng hợp nhất sẵn có từ Spec 019 với đầy đủ metadata chống gửi trùng (Idempotency) và Cooldown 3 giờ.
- **Testing**: `pytest` (Backend Unit & Integration Tests)
- **Target Platform**: Linux Server / Docker Container
- **Project Type**: Web Application & Background Automation Job
- **Timezone**: `Asia/Ho_Chi_Minh` (UTC+7) cho mọi phép toán so sánh thời gian và deadline.
- **Constraints**: Không phá vỡ kiến trúc Clean Architecture, không tạo migration thừa, không sửa đổi logic hiện có của các Task Scanners khác.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

- **Principle I (Clean Architecture & Practical DDD Boundaries)**: **PASS**  
  - Domain Layer: `TaskType.MEETING` và `Notification.create_deadline_reminder` xử lý thuần túy logic domain, zero dependencies bên ngoài.
  - Application Layer: `UpcomingMeetingTaskScanner` kế thừa `BaseTaskScanner`, chỉ đảm nhiệm việc quét và trả về `ScannedCandidateTask`. `ScanAndSendRemindersUseCase` giữ nguyên vai trò Orchestrator.
  - Infrastructure Layer: Tận dụng `MeetingRepository.get_all_with_participants` và `NotificationRepository` để truy vấn dữ liệu. Không viết raw SQL trong Use Case.
- **Principle II (Dependency Injection with Dishka)**: **PASS**  
  - Đăng ký `UpcomingMeetingTaskScanner` và inject trực tiếp vào `ScanAndSendRemindersUseCase` thông qua `ReminderModuleProvider` (`backend/app/reminder/providers.py`).
- **Principle III (Unified UTC+7 Timezone & DateTime Integrity)**: **PASS**  
  - Mọi mốc thời gian họp (`meeting.start_time`) và thời điểm quét (`now`) đều sử dụng chuẩn `get_current_utc7_time()`.
- **Principle IV (Event-Driven Decoupling & Asynchronous Handlers)**: **PASS**  
  - Phân phối thông báo đa kênh (Discord DM, Web Push) diễn ra bất đồng bộ qua `ReminderDispatcher`.
- **Principle VII (Strict Single-Responsibility Use Cases & Scanners)**: **PASS**  
  - Mỗi scanner đặt trong 1 file độc lập (`upcoming_meeting_scanner.py`), chỉ có một phương thức chính `scan_pending_tasks(self, now: datetime)`.
  - Không gộp chung logic với `MeetingEvaluationTaskScanner`.
- **Principle X (Zero Redundant Backward Compatibility & No Duplicate API Surface)**: **PASS**  
  - Không tạo alias hay API thừa. Tái sử dụng trực tiếp các endpoint sẵn có (`/api/v1/reminders/trigger`, `/api/v1/notifications/my`).

## Project Structure

### Documentation (this feature)

```text
specs/023-upcoming-meeting-reminder/
├── spec.md              # Đặc tả nghiệp vụ & User Stories
├── checklists/
│   └── requirements.md  # Checklist xác thực chất lượng đặc tả
├── plan.md              # Kế hoạch kiến trúc (File hiện tại)
├── research.md          # Phân tích kỹ thuật & các quyết định kiến trúc
├── data-model.md        # Thiết kế Entity & Ma trận lọc trạng thái
├── contracts/           # API Contracts & Embed JSON Schemas
│   ├── meeting-discord-embed.json
│   └── meeting-notification-response.json
├── quickstart.md        # Hướng dẫn kiểm thử & chạy thử nghiệm
└── tasks.md             # Danh sách phân rã tasks (tạo bởi /speckit-tasks)
```

### Source Code Impact

```text
backend/app/
├── meeting/
│   └── infrastructure/
│       └── repository.py                 # Tận dụng get_all_with_participants & get_upcoming_meetings
└── reminder/
    ├── domain/
    │   └── entity.py                     # Thêm TaskType.MEETING, tinh chỉnh Notification.create_deadline_reminder
    ├── application/
    │   ├── scanners/
    │   │   ├── base_scanner.py           # Interface BaseTaskScanner sẵn có
    │   │   └── upcoming_meeting_scanner.py # MỚI: Scanner chuyên biệt quét buổi họp sắp diễn ra
    │   ├── embed_builder.py              # Thêm format embed riêng cho TaskType.MEETING
    │   ├── reminder_dispatcher.py        # Giữ nguyên, đã hỗ trợ đa kênh (Web + Discord + Web Push)
    │   └── scan_and_send_reminders_use_case.py # Giữ nguyên, nhận scanner mới qua constructor
    └── providers.py                      # Đăng ký UpcomingMeetingTaskScanner vào Dishka DI Container

backend/tests/
└── test_upcoming_meeting_scanner.py      # MỚI: Unit test cho UpcomingMeetingTaskScanner
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| *Không có vi phạm* | Kiến trúc tận dụng 100% nền tảng sẵn có | Không phát sinh technical debt |
