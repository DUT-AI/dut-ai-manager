# Implementation Plan: Unified Multi-Channel Notifications

**Branch**: `024-unified-multi-channel-notifications` | **Date**: 2026-10-22 | **Spec**: [specs/024-unified-multi-channel-notifications/spec.md](spec.md)

**Input**: Feature specification from `/specs/024-unified-multi-channel-notifications/spec.md`

## Summary

Tái cấu trúc và hợp nhất toàn bộ hệ thống phát thông báo trong `dut-ai-manager` thành **Unified Notification Hub**.
- Đưa logic điều phối phát thông báo đa kênh (**In-App DB, Discord Bot, Zalo Bot, Web Push PWA**) về một cổng trung tâm `UnifiedNotificationDispatcher` tại tầng Shared Application/Infrastructure.
- Tự động lưu 100% các sự kiện nghiệp vụ (Meeting, Homework, Violation, Bonus Point, Billing, Task Reminder) vào cơ sở dữ liệu In-App (`notifications`), đồng thời phát tán bất đồng bộ và cách ly lỗi đến các kênh mạng xã hội/thiết bị của người dùng.
- Chuẩn hóa DTO `NotificationPayload` và Entity Factory methods để việc thêm loại thông báo mới trong tương lai chỉ mất vài dòng code.

---

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Dishka DI, Pydantic V2, aiohttp (Discord & Zalo Client), pywebpush (RFC 8292)
**Storage**: PostgreSQL / SQLite (bảng `notifications` và `push_subscriptions`)
**Testing**: pytest, pytest-asyncio, unittest.mock
**Target Platform**: Linux / macOS Docker container & Web/Zalo Mini App Clients
**Project Type**: Backend Web Service (Clean Architecture / Modular Monolith)
**Performance Goals**: Dispatch In-App trong < 50ms, phát tán song song đa kênh ngoài trong < 3 giây
**Constraints**: Fault Isolation (lỗi kênh ngoài không được chặn luồng nghiệp vụ DB), UTC+7 timezone cho toàn bộ hiển thị
**Scale/Scope**: ~10 domain event handlers, ~5 scanner classes, phục vụ toàn bộ thành viên CLB

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
|---|---|---|
| **I. Clean Architecture & Practical DDD** | Tách rõ Domain (`Notification` Entity), Shared Infra (`NotificationChannel` Adapters, `UnifiedNotificationDispatcher`), Presentation (`NotificationController`). | **PASS** |
| **II. Dependency Injection with Dishka** | Toàn bộ Dispatcher, Channels, và Use Cases được đăng ký qua Dishka Provider (`app/shared/providers.py`). | **PASS** |
| **III. Unified UTC+7 Timezone** | Thời gian tạo và hiển thị trong Embed/Zalo/Web Push sử dụng UTC+7. | **PASS** |
| **IV. Event-Driven Decoupling** | Phân phối external channels (Discord, Zalo, Web Push) chạy ngầm (`asyncio.create_task`), không chặn transaction DB. | **PASS** |
| **V. Non-Null Contract DTOs** | API response tuân thủ `ApiResponse[T]` với pagination meta đầy đủ. | **PASS** |
| **VII. Strict Single-Responsibility Use Cases** | Các use case truy vấn và thao tác thông báo (GetMy, Read, ReadAll) đều tách riêng từng file `*_use_case.py`. | **PASS** |
| **IX. Pure Composition Over Base Use Cases** | Không dùng Base Use Case. Sử dụng Adapter Pattern (`NotificationChannel`) và DI composition. | **PASS** |
| **X. Zero Redundant Backward Compatibility** | Giữ nguyên API contract cho frontend hiện tại (`/notifications/my`), refactor trực tiếp các call sites nội bộ không để lại alias thừa. | **PASS** |

---

## Project Structure

### Documentation (this feature)

```text
specs/024-unified-multi-channel-notifications/
├── spec.md              # Đặc tả nghiệp vụ
├── plan.md              # Kế hoạch kiến trúc (File này)
├── research.md          # Phân tích hiện trạng & Quyết định kỹ thuật
├── data-model.md        # Thiết kế thực thể & sơ đồ trạng thái
├── quickstart.md        # Hướng dẫn kiểm thử và kịch bản xác thực
├── contracts/
│   └── notification-hub-api.md  # Hợp đồng API & Service Interfaces
└── checklists/
    └── requirements.md  # Checklist kiểm định chất lượng spec
```

### Source Code Changes

```text
backend/app/
├── shared/
│   ├── infrastructure/
│   │   ├── notification_payload.py          # [MODIFY] Mở rộng NotificationPayload & NotificationCategory
│   │   ├── notification/                    # [NEW] Thư mục Adapter Channels
│   │   │   ├── __init__.py
│   │   │   ├── channel.py                   # [NEW] Protocol NotificationChannel & ChannelDeliveryResult
│   │   │   ├── in_app_channel.py            # [NEW] InAppNotificationChannel (lưu DB)
│   │   │   ├── discord_channel.py           # [NEW] DiscordNotificationChannel (gửi DM/Room kèm Meme)
│   │   │   ├── zalo_channel.py              # [NEW] ZaloNotificationChannel (gửi Zalo Bot)
│   │   │   ├── web_push_channel.py          # [NEW] WebPushNotificationChannel (bắn PWA Push)
│   │   │   └── dispatcher.py                # [NEW] UnifiedNotificationDispatcher (Hub điều phối)
│   │   └── notification_service.py          # [REPLACE/REFACTOR] Chuyển đổi sang delegate cho Unified Dispatcher
│   └── providers.py                         # [MODIFY] Đăng ký Dispatcher và Channels vào Dishka
├── reminder/
│   ├── domain/
│   │   └── entity.py                        # [MODIFY] Thêm Notification.create(...) và tái cấu trúc create_deadline_reminder
│   └── application/
│       └── reminder_dispatcher.py           # [MODIFY] Sử dụng UnifiedNotificationDispatcher cho đa kênh
├── meeting/application/event_handlers.py    # [MODIFY] Chuyển sang dùng UnifiedNotificationDispatcher
├── homework/application/event_handlers.py   # [MODIFY] Chuyển sang dùng UnifiedNotificationDispatcher
├── violation/notification_handler.py        # [MODIFY] Chuyển sang dùng UnifiedNotificationDispatcher
├── bonus_point/notification_handler.py      # [MODIFY] Chuyển sang dùng UnifiedNotificationDispatcher
└── billing/application/notification_handler.py # [MODIFY] Chuyển sang dùng UnifiedNotificationDispatcher
```

---

## Complexity Tracking

*Không có vi phạm hiến pháp nào cần giải trình.* Kiến trúc áp dụng trực tiếp Strategy/Adapter Pattern chuẩn hóa theo Clean Architecture.
