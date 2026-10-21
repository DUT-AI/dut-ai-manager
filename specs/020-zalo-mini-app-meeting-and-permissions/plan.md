# Implementation Plan: Đồng Bộ Tính Năng Lịch Meeting & Quản Lý Đơn Phép Trên Zalo Mini App

**Branch**: `020-zalo-mini-app-meeting-and-permissions` | **Date**: 2026-10-21 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/020-zalo-mini-app-meeting-and-permissions/spec.md`

## Summary

Đồng bộ toàn diện trải nghiệm người dùng từ Web sang Zalo Mini App cho 2 phân hệ trọng yếu:
1. **Lịch Meeting**: Bổ sung trang chi tiết chuyên biệt `MeetingDetailPage` (`/meetings/:id`) với Hero Card, hàng chỉ số sĩ số, tab Người tham gia (kèm Check-in và cập nhật trạng thái Host), và các tab Đánh giá buổi họp (Trainee Evaluation, Trainer Evaluation, Overall Evaluation).
2. **Quản lý Đơn phép**: Chuẩn hóa danh sách hiển thị toàn bộ đơn kèm bộ lọc đa năng (theo danh mục, trạng thái, người tạo/đơn của tôi) tương tự Web, hoàn thiện form nộp đơn đổi ca (`CHANGE_MEETING`) hiển thị số ghế trống theo thời gian thực.

## Technical Context

- **Language/Version**: TypeScript 5.x, React 18
- **Primary Dependencies**: `zmp-ui`, `zmp-sdk`, `@tanstack/react-query` v5, `react-router-dom` v6, `axios`, `dayjs`
- **Storage**: In-memory React Query cache & ZMP Storage (Token)
- **Target Platform**: Zalo Super App Webview (Mobile First)
- **Project Type**: Mobile Mini App
- **Constraints**: Kích thước màn hình nhỏ, ưu tiên thao tác chạm (touch friendly), giao diện ZaUI đồng bộ, thời gian tải dữ liệu < 1.5s.

## Constitution Check

- *Security Check*: Tái sử dụng Axios Bearer auth token, không hardcode secret.
- *Compatibility*: Tương thích với Backend API FastAPI hiện hữu của hệ thống.
- *User Experience*: Tối ưu hiển thị responsive, giữ chân thanh điều hướng dưới (BottomNavigation) hoặc Header ZaUI chuẩn.

## Project Structure

### Documentation (this feature)

```text
specs/020-zalo-mini-app-meeting-and-permissions/
├── spec.md              # Feature specification & clarifications
├── plan.md              # Implementation plan (this file)
├── research.md          # Technical research & architectural decisions
├── data-model.md        # Entities & component mapping
├── quickstart.md        # E2E validation & testing guide
├── contracts/
│   └── api-contracts.md # Backend API specifications
└── checklists/
    └── requirements.md  # Quality validation checklist
```

### Source Code Changes

```text
zalo-mini-app/dut-manager/
├── src/
│   ├── constants/
│   │   └── paths.ts                    # Add MEETING_DETAIL path
│   ├── app.tsx                         # Register route /meetings/:id
│   ├── services/api/
│   │   ├── meeting.service.ts          # Add evaluation & participant update APIs
│   │   └── permission.service.ts       # Ensure full filter support
│   ├── pages/
│   │   ├── MeetingDetailPage.tsx       # New full Meeting Detail page
│   │   ├── CalendarPage.tsx            # Update click action to navigate to /meetings/:id
│   │   └── PermissionsPage.tsx         # Update filters & layout like Web
│   └── features/
│       ├── schedule/
│       │   ├── MeetingHeroCard.tsx     # Hero summary card
│       │   ├── MeetingStatsCard.tsx    # Attendance statistics row
│       │   ├── MeetingParticipantsTab.tsx # Participants list & check-in
│       │   └── MeetingEvaluationTab.tsx   # Trainee/Trainer evaluation tab
│       └── permission_request/
│           ├── PermissionFilters.tsx   # Extended filters (Category & Mine/All)
│           └── PermissionFormModal.tsx # Enhanced CHANGE_MEETING seat calculations
```

## Plan Phases

- **Phase 0: Research & Context** (Hoàn thành) -> `research.md`
- **Phase 1: Design & Contracts** (Hoàn thành) -> `data-model.md`, `contracts/`, `quickstart.md`, `plan.md`
- **Phase 2: Task Breakdown** (Sẵn sàng) -> Tiếp tục bằng `/speckit-tasks`
