# Implementation Plan: PWA Mobile Install Top Banner

**Branch**: `048-pwa-install-banner` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from [`specs/048-pwa-install-banner/spec.md`](./spec.md)

## Summary

Xây dựng thanh banner trên cùng (Top Banner) khuyến khích cài đặt PWA dành riêng cho người dùng duyệt web bằng thiết bị di động (Mobile/Tablet) chưa cài đặt ứng dụng. Thanh banner hiển thị xếp tầng cùng thanh Bật thông báo đẩy hiện tại ([`PushBanner.tsx`](file:///Users/nguyenhuynh/Documents/dut-ai-manager/frontend/src/features/pwa/components/PushBanner.tsx)), có thiết kế đồng nhất và tinh gọn, duy nhất có nút hành động "Cài đặt ngay" (không có nút "Để sau"). Hỗ trợ gọi prompt cài đặt native trên Android/Chromium và mở popup hướng dẫn trực quan 2 bước trên iOS Safari.

## Technical Context

**Language/Version**: TypeScript 5.x / React 18
**Primary Dependencies**: Ant Design 5.x (`Button`, `Modal`, `Typography`), Tailwind CSS, `@ant-design/icons` (`DownloadOutlined`, `AppleOutlined`, `ExportOutlined`, `PlusSquareOutlined`)
**Storage**: Client memory (`useState`, `matchMedia`), không yêu cầu lưu trữ server hay database
**Testing**: Unit tests với Vitest / Playwright component testing
**Target Platform**: Mobile Web Browsers (Chrome Android, Samsung Internet, iOS Safari)
**Project Type**: Frontend Client Feature (Web App)
**Performance Goals**: Render tức thì sau khi trang tải (<50ms), chiều cao banner cố định <= 48px, zero layout shift (CLS < 0.05)
**Constraints**: 
- Chỉ hiển thị trên điện thoại / máy tính bảng; tuyệt đối không hiển thị trên máy tính (Desktop/Laptop).
- Chỉ có lựa chọn tải về (không có nút dismiss "Để sau").
- Tự động ẩn vĩnh viễn khi ứng dụng chạy ở chế độ Standalone PWA.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Evaluation | Status |
|---|---|---|
| **I. Clean Architecture & Boundaries** | Hoàn toàn nằm ở Presentation Layer phía Frontend, không làm biến dạng nghiệp vụ backend | **PASS** |
| **VIII. Frontend Component Modularity** | Phân tách rành mạch: Hook thiết bị (`usePwaInstall`), Top Banner (`PwaInstallBanner`), Modal hướng dẫn (`IosInstallModal`), container xếp tầng tại `App.tsx` | **PASS** |
| **V. Non-Null Contract DTOs** | Không phát sinh API contract mới, các trạng thái boolean của hook đều là primitive strictly-typed (`boolean`) | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/048-pwa-install-banner/
├── plan.md                                                  # File kế hoạch hiện tại
├── research.md                                              # Nghiên cứu thiết bị di động, PWA standalone, Chromium prompt & iOS Safari
├── data-model.md                                            # Cấu trúc UI state và ma trận chuyển trạng thái
├── quickstart.md                                            # Hướng dẫn kiểm thử 4 kịch bản (Desktop, Android, iOS, Xếp tầng)
├── contracts/
│   └── pwa-install-banner-contracts.yaml                    # Đặc tả giao diện và điều kiện kích hoạt banner
└── tasks.md                                                 # Sẽ được tạo ở lệnh /speckit-tasks
```

### Source Code (repository root)

```text
frontend/src/
├── features/pwa/
│   ├── hooks/
│   │   ├── usePwaInstall.ts                                 # Nâng cấp phát hiện isMobile, isIos, isStandalone, isInstallable
│   │   └── useWebPush.ts                                    # Đã có sẵn (quản lý Push Notification)
│   ├── components/
│   │   ├── PwaInstallBanner.tsx                             # [MỚI] Thanh Top Banner mỏng nhẹ trên cùng (không có nút dismiss)
│   │   ├── IosInstallModal.tsx                              # [MỚI] Modal hướng dẫn 2 bước trực quan cho iOS Safari
│   │   ├── PushBanner.tsx                                   # Đã có sẵn (thanh Bật thông báo đẩy trên cùng)
│   │   └── index.ts                                         # Re-export PwaInstallBanner và PushBanner
├── App.tsx                                                  # Tích hợp xếp tầng: <PwaInstallBanner /> + {isAuthenticated && <PushBanner />}
```

## Complexity Tracking

> Không có vi phạm kiến trúc cần ngoại lệ.

| Metric | Planned Value | Rationale |
|---|---|---|
| Component Dependencies | 2 files mới | Đảm bảo nguyên tắc Single-Responsibility UI |
| Bundle Impact | < 2KB gzipped | Tái sử dụng Ant Design & Tailwind CSS có sẵn |
