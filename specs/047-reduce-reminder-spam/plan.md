# Implementation Plan: Tái cấu trúc Nghiệp vụ Nhắc nhở Theo Mốc Đếm Ngược & Loại bỏ Spam Thông báo

**Branch**: `047-reduce-reminder-spam` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/047-reduce-reminder-spam/spec.md`

## Summary

Tái cấu trúc toàn diện nghiệp vụ nhắc nhở thời hạn công việc (Reminder Engine) nhằm triệt tiêu hơn 70% lượng thông báo làm phiền khách hàng/thành viên. Chuyển đổi từ cơ chế quét lai (Hybrid) kết hợp 4 khung giờ cố định (`08:00`, `12:00`, `19:30`, `22:00`) sang cơ chế thuần đếm ngược (Pure Countdown Offsets) với 3 mốc chuẩn: **24h (`OFFSET_1D`)**, **4h (`OFFSET_4H`)**, và **1h (`OFFSET_1H`)**. Đồng thời tạm dừng gửi thông báo qua kênh Zalo Bot (Mute Zalo Bot Channel) mà vẫn bảo toàn 100% mã nguồn tích hợp Zalo hiện có.

## Technical Context

**Language/Version**: Python 3.12+ (Backend)

**Primary Dependencies**: FastAPI, Pydantic v2, Dishka (Dependency Injection), APScheduler (Cron Job), SQLAlchemy 2.0

**Storage**: PostgreSQL (Bảng `notifications`), bảo toàn tương thích ngược cho các bản ghi cũ

**Testing**: `pytest`, `pytest-asyncio`

**Target Platform**: Docker / Linux Server / macOS Dev Environment

**Project Type**: Backend Web Service & Background Job Scheduler

**Performance Goals**: Tiến trình quét `scan_and_send_reminders` hoàn tất trong dưới 2 giây cho toàn bộ 4 scanners (Homework, Duty, Meeting, Meeting Evaluation)

**Constraints**:
- Tuân thủ múi giờ chuẩn UTC và hiển thị UTC+7 (Asia/Ho_Chi_Minh).
- Giữ nguyên các giá trị enum cũ (`FIXED_*`, `OFFSET_2D`, `OFFSET_12H`) trong Python code để khi truy vấn ORM các bản ghi thông báo trong quá khứ không bị lỗi deserialization.
- Tuyệt đối không xóa mã nguồn Zalo Bot Client và Zalo Channel; ngưng phát tán qua cờ cấu hình/bộ lọc kênh.

**Scale/Scope**: ~100 thành viên hoạt động, 4 loại nhiệm vụ (Homework, Duty, Meeting, Meeting Evaluation)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú tuân thủ |
|---|---|---|
| **Principle I: Clean Architecture & Practical DDD** | ✅ PASS | Logic tính toán mốc thời gian nằm trọn vẹn trong Domain Entity `ReminderStage` (`domain/entity.py`). Tầng Application chỉ ủy quyền điều phối. |
| **Principle II: Dependency Injection with Dishka** | ✅ PASS | Giữ nguyên DI injection của `ZaloNotificationChannel` và các collaborators trong Dishka provider, không phá vỡ đồ thị phụ thuộc. |
| **Principle III: Enterprise UTC & Vietnam Display** | ✅ PASS | Mọi so sánh thời gian trong `calculate_matching_stages` chuẩn hóa về timezone-aware UTC. |
| **Principle IV: Event-Driven & Async Decoupling** | ✅ PASS | Phân phối thông báo đa kênh tiếp tục chạy nền bất đồng bộ (`asyncio.create_task`). |
| **Principle V: API Backward Compatibility** | ✅ PASS | Bảo tồn các thành viên legacy của enum `ReminderStage` để không làm crash API đọc danh sách thông báo lịch sử `GET /api/v1/notifications/my`. |
| **Principle VI: Idempotency & Network Resilience** | ✅ PASS | Kiểm tra trùng lặp (Deduplication) theo `(task_type, task_id, user_id, stage)` đảm bảo mỗi mốc đếm ngược chỉ gửi đúng 1 lần. |
| **Principle XIV: No Fake Optionals & Fail-Fast** | ✅ PASS | Không tạo các optional giả hoặc fallback ngầm sai lệch giá trị. |

## Project Structure

### Documentation (this feature)

```text
specs/047-reduce-reminder-spam/
├── spec.md                     # Feature specification
├── plan.md                     # This implementation plan
├── research.md                 # Architectural & business decisions
├── data-model.md               # Domain entities & enum definitions
├── quickstart.md               # Automated testing & verification guide
├── contracts/
│   └── reminder-scan-contracts.yaml # API & DTO contracts
└── checklists/
    └── requirements.md         # Specification quality checklist
```

### Source Code Impact (repository root)

```text
backend/
├── app/
│   ├── core/
│   │   └── config.py                                       # Thêm cờ ENABLE_ZALO_NOTIFICATION: bool = False
│   ├── reminder/
│   │   ├── domain/
│   │   │   └── entity.py                                   # Tinh gọn ReminderStage & calculate_matching_stages thuần đếm ngược
│   │   └── application/
│   │       ├── reminder_dispatcher.py                      # Giữ nguyên cấu trúc thông báo quen thuộc
│   │       └── scanners/
│   │           ├── base_scanner.py                         # Gọi calculate_matching_stages
│   │           ├── homework_scanner.py                     # Quét theo mốc đếm ngược
│   │           ├── duty_scanner.py                         # Quét theo mốc đếm ngược
│   │           ├── upcoming_meeting_scanner.py             # Quét theo mốc đếm ngược
│   │           └── meeting_evaluation_scanner.py           # Quét theo mốc đếm ngược
│   └── shared/
│       └── infrastructure/
│           └── notification/
│               ├── dispatcher.py                           # Tôn trọng cờ ENABLE_ZALO_NOTIFICATION khi phát tán đa kênh
│               └── zalo_channel.py                         # Trả về status="DISABLED" khi kênh Zalo bị tắt (giữ nguyên 100% code)
└── tests/
    ├── unit/
    │   └── test_reminder_use_cases.py                      # Cập nhật & bổ sung unit test cho mốc 24h, 4h, 1h và mute Zalo
    └── integration/
        └── test_reminder_integration.py                    # Kiểm thử tích hợp tiến trình quét & chống trùng
```

**Structure Decision**: Thay đổi tập trung hoàn toàn ở `backend/` trong module `app/reminder/` và `app/shared/infrastructure/notification/`. Không làm thay đổi schema database và không ảnh hưởng đến giao diện `frontend/`.

## Complexity Tracking

*Không có vi phạm hiến pháp cần giải trình.*
