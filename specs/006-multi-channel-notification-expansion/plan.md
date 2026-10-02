# Implementation Plan: Nâng Cấp Hệ Thống Thông Báo Đa Kênh (Discord & Zalo) & Tích Hợp Assets Meme

**Branch**: `006-multi-channel-notification-expansion` | **Date**: 2026-10-02 | **Spec**: [`spec.md`](./spec.md)

**Input**: Feature specification from [`specs/006-multi-channel-notification-expansion/spec.md`](./spec.md)

## Summary

Nâng cấp và thống nhất toàn bộ hệ thống gửi thông báo đa kênh (Discord + Zalo) cho toàn bộ 6 use case hiện hữu trong hệ thống (`Billing/Payment`, `Homework`, `Violation`, `Bonus Point`, `Meeting`, `Permission Request`). Tích hợp tự động hóa gửi kèm hình ảnh meme sinh động từ kho `backend/app/assets` qua Static Assets Serving của FastAPI, đóng gói kiến trúc phân phối qua `NotificationService` chuẩn hóa, tách biệt lỗi (Fault Isolation) và áp dụng cơ chế Retry tự động.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: FastAPI, Dishka (DI), aiohttp, Starlette StaticFiles, zalo_bot, Loguru  
**Storage**: PostgreSQL / SQLite (sử dụng các trường ID sẵn có trên bảng `users`: `discord_id`, `zalo_bot_id`)  
**Testing**: pytest, pytest-asyncio, unittest.mock  
**Target Platform**: Linux / macOS Docker Server (UTC+7 Timezone)  
**Project Type**: Web Service / API Backend  
**Performance Goals**: Phát sự kiện và đưa vào background task trong < 50ms; gửi tin nhắn đến Discord & Zalo < 3s  
**Constraints**: Zero Blocking trên API response; 100% Fault Isolation giữa các kênh; Fallback an toàn khi link ảnh lỗi  
**Scale/Scope**: Áp dụng cho toàn bộ thành viên CLB (hàng trăm người dùng), 6 domain nghiệp vụ chính  

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Clean Architecture & Practical DDD**: Tách biệt rõ ràng Domain Events, Use Cases, và Infrastructure Notification Services.
- [x] **II. Dependency Injection with Dishka**: `NotificationService`, `DiscordService`, `ZaloBotClient` được đăng ký và inject qua Dishka providers (`InfrastructureProvider`).
- [x] **III. Unified UTC+7 Timezone**: Tất cả timestamp hiển thị trên Discord Embeds/Zalo Messages sử dụng UTC+7.
- [x] **IV. Event-Driven Decoupling**: Mọi thông báo được kích hoạt bất đồng bộ qua `EventBus` và chạy ngầm (Non-blocking background tasks).
- [x] **V. API Backward Compatibility**: Không làm thay đổi signature hay response format của các API endpoints hiện có.
- [x] **VII. Single-Responsibility Use Cases**: Mỗi use case/handler nằm trong file riêng biệt với chức năng duy nhất.

---

## Project Structure

### Documentation (this feature)

```text
specs/006-multi-channel-notification-expansion/
├── spec.md                  # Đặc tả yêu cầu tính năng
├── plan.md                  # Kế hoạch thực thi (tệp này)
├── research.md              # Nghiên cứu giải pháp kỹ thuật Phase 0
├── data-model.md            # Mô hình dữ liệu & Domain Events Phase 1
├── quickstart.md            # Hướng dẫn kiểm thử nhanh Phase 1
├── contracts/               # Giao diện & Hợp đồng dịch vụ Phase 1
│   └── notification-service-contract.md
├── checklists/
│   └── requirements.md      # Checklist nghiệm thu spec
└── tasks.md                 # Danh sách tasks Phase 2 (tạo bởi /speckit-tasks)
```

### Source Code (repository root)

```text
backend/app/
├── assets/                                     # Kho ảnh meme có sẵn
│   ├── meme-hoc-bai.webp
│   ├── meme-xin-tien.jpeg
│   ├── meme-doi-no-2.jpg
│   └── ...
├── billing/
│   ├── domain/
│   │   └── events.py                           # [MỚI] InvoiceCreated, InvoicePaid
│   ├── application/
│   │   ├── use_cases.py                        # Cập nhật phát event khi tạo / thanh toán hóa đơn
│   │   └── notification_handler.py             # [MỚI] BillingNotificationHandler
│   └── providers.py
├── shared/
│   ├── infrastructure/
│   │   ├── notification_payload.py             # [MỚI] NotificationPayload Value Object
│   │   ├── notification_service.py             # [MỚI] NotificationService implementation
│   │   └── asset_helper.py                     # [MỚI] Helper tạo URL công khai cho file trong app/assets
│   └── providers.py                            # Đăng ký NotificationService vào Dishka
├── homework/
│   └── application/
│       └── event_handlers.py                   # Nâng cấp gửi meme qua NotificationService
├── violation/
│   └── notification_handler.py                 # Nâng cấp gửi meme qua NotificationService
├── bonus_point/
│   └── notification_handler.py                 # Nâng cấp gửi meme qua NotificationService
├── meeting/
│   └── application/
│       └── event_handlers.py                   # Nâng cấp gửi meme qua NotificationService
├── permission_request/
│   └── application/
│       └── event_handlers.py                   # Nâng cấp gửi meme qua NotificationService
├── core/
│   └── events.py                               # Đăng ký BillingNotificationHandler vào bootstrap_events
└── main.py                                     # Mount StaticFiles cho /static/assets
```

**Structure Decision**: Cấu trúc tuân thủ Clean Architecture chuẩn của dự án: Bổ sung `NotificationService` dùng chung trong `app/shared/infrastructure/`, mount static path trong `main.py`, và nâng cấp các handler của từng domain để thống nhất định dạng.

---

## Complexity Tracking

> Không có vi phạm Constitution cần giải trình. Kiến trúc tối giản hóa mã nguồn hiện có bằng cách gom logic trùng lặp vào `NotificationService`.
