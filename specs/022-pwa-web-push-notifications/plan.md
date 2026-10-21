# Implementation Plan: PWA & Web Push Notification System

**Branch**: `022-pwa-web-push-notifications` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/022-pwa-web-push-notifications/spec.md`

---

## Summary

Triển khai khả năng biến Web Frontend (`frontend/`) thành ứng dụng **Progressive Web App (PWA)** có thể cài đặt trực tiếp ra màn hình chính thiết bị di động (Android & iOS 16.4+), đồng thời tích hợp hệ thống gửi thông báo đẩy **Web Push Notifications (VAPID RFC 8292)** từ Backend FastAPI (`backend/app/reminder`). Khi có sự kiện (Họp, Bài tập, Trực nhật), hệ thống tự động đẩy thông báo ra màn hình khóa thiết bị với chi phí 0 VNĐ, không phụ thuộc vào Zalo OA hay duyệt store.

---

## Technical Context

- **Language/Version**:
  - Backend: Python 3.12+
  - Frontend: TypeScript 5.x / React 19 / Vite 5+
- **Primary Dependencies**:
  - Backend: FastAPI, SQLModel / SQLAlchemy 2.0, Dishka DI, `pywebpush` (chuẩn VAPID RFC 8292), `pydantic-settings`
  - Frontend: React 19, Vite, TanStack React Query v5, Tailwind CSS v4, Ant Design
- **Storage**:
  - PostgreSQL (Bảng `push_subscriptions` liên kết khóa ngoại với `users.id`)
  - Client Cache / Service Worker Cache Storage
- **Testing**:
  - Backend: `pytest`, `pytest-asyncio`
  - Frontend: `npm run build` (TypeScript compiler check), Playwright E2E
- **Target Platform**:
  - Mobile: Android (Chrome/Edge/Samsung Internet), iOS 16.4+ (Safari Add to Home Screen)
  - Desktop: Windows/macOS (Chrome, Edge, Safari, Firefox)
- **Performance Goals**:
  - Độ trễ gửi và hiển thị thông báo đẩy: < 5 giây từ lúc phát sự kiện trên server.
  - Tải trọng Service Worker `sw.js`: < 30 KB.
  - Đăng ký thiết bị (Subscription registration): < 500 ms.
- **Constraints**:
  - Bắt buộc chạy qua giao thức bảo mật HTTPS (yêu cầu của Service Worker & Web Push API).
  - Tuân thủ nghiêm ngặt Hiến pháp dự án (`Clean Architecture`, `Dishka DI`, `UTC+7`, `Single-Responsibility Use Cases`).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Hiến pháp (Constitution Principle) | Trạng thái | Đánh giá tuân thủ (Compliance Assessment) |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | **PASS** | Tách lớp rõ ràng trong `backend/app/reminder/`: Entity `PushSubscription`, Repository `PushSubscriptionRepository`, Use Cases độc lập trong `application/`. |
| **II. Dependency Injection with Dishka** | **PASS** | Đăng ký `WebPushService`, Repository và các Use Case vào `backend/app/reminder/providers.py` và inject bằng `@inject` qua `FromDishka[...]`. |
| **III. Unified UTC+7 Timezone** | **PASS** | Mọi mốc thời gian `created_at`, `last_used_at` đều sử dụng `get_current_utc7_time()`. |
| **IV. Event-Driven Decoupling** | **PASS** | Thao tác gửi Web Push qua mạng internet tới máy chủ Apple/Google được kích hoạt bất đồng bộ qua Background Task / Event Handler, tuyệt đối không block transaction chính. |
| **V. API Envelope & Non-Null Contracts** | **PASS** | Mọi API endpoint tuân thủ chuẩn phong bì `ApiResponse[T]` thống nhất. |
| **VII. Strict Single-Responsibility Use Cases** | **PASS** | Mỗi Use Case nằm trong 1 tệp riêng biệt chỉ có 1 phương thức public `execute`: `register_push_subscription_use_case.py`, `unregister_push_subscription_use_case.py`, `send_web_push_notification_use_case.py`. |
| **VIII. Frontend Component Modularity** | **PASS** | Các UI subcomponents như `PwaInstallBanner`, `PushPermissionPrompt` được tách thành các file độc lập trong `frontend/src/features/pwa/components/`. |
| **X. Zero Redundant Backward Compatibility** | **PASS** | Không tạo alias hoặc wrapper thừa thãi; gọi trực tiếp các hook/endpoint chuẩn tắc. |

---

## Project Structure

### Documentation (this feature)

```text
specs/022-pwa-web-push-notifications/
├── plan.md              # Kế hoạch kiến trúc kỹ thuật chi tiết
├── research.md          # Kết quả nghiên cứu VAPID, Service Worker, iOS PWA
├── data-model.md        # Mô hình thực thể PushSubscription & Payload schema
├── quickstart.md        # Kịch bản kiểm thử đầu-cuối trên Android và iOS
└── contracts/
    └── push-api-contracts.md # Đặc tả chi tiết các endpoint API Web Push
```

### Source Code (repository root)

```text
backend/app/reminder/
├── domain/
│   ├── entity.py                    # Bổ sung thực thể PushSubscription
│   └── repository.py                # Interface PushSubscriptionRepository
├── infrastructure/
│   ├── models.py                    # SQLModel / ORM model push_subscriptions
│   ├── repository.py                # Implementation PushSubscriptionRepository
│   └── web_push_service.py          # Service bọc thư viện pywebpush & VAPID keys
├── application/
│   ├── dtos.py                      # PushSubscriptionRequestDto, PushPublicKeyDto
│   ├── register_push_subscription_use_case.py   # Use Case đăng ký thiết bị
│   ├── unregister_push_subscription_use_case.py # Use Case hủy đăng ký thiết bị
│   └── send_web_push_notification_use_case.py   # Use Case đẩy thông báo tới user
├── controller.py                    # Endpoint /push-public-key, /push-subscriptions, /test-push
└── providers.py                     # Đăng ký Dishka Provider

frontend/
├── public/
│   ├── manifest.json                # PWA Manifest (name, icons, display: standalone)
│   ├── sw.js                        # Service Worker xử lý sự kiện push & notificationclick
│   └── icons/                       # Icons đa kích cỡ 192x192, 512x512 cho PWA
├── src/
│   ├── features/pwa/
│   │   ├── hooks/
│   │   │   ├── usePwaInstall.ts     # Hook lắng nghe beforeinstallprompt (Android/iOS)
│   │   │   └── useWebPush.ts        # Hook đăng ký Service Worker & pushManager.subscribe()
│   │   ├── components/
│   │   │   ├── PwaInstallPrompt.tsx # Banner/Modal hướng dẫn cài đặt PWA
│   │   │   └── PushBanner.tsx       # Banner đề xuất bật thông báo đẩy
│   │   └── services/
│   │       └── pushService.ts       # Gọi API backend đăng ký/hủy token VAPID
│   └── App.tsx                      # Tích hợp đăng ký Service Worker và PwaInstallPrompt
```

---

## Complexity Tracking

Không có vi phạm Hiến pháp nào cần biện minh. Toàn bộ giải pháp tuân thủ kiến trúc chuẩn của dự án.
