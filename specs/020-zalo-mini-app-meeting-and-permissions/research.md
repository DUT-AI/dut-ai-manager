# Research: Đồng Bộ Tính Năng Lịch Meeting & Quản Lý Đơn Phép Trên Zalo Mini App

**Feature**: `020-zalo-mini-app-meeting-and-permissions`  
**Date**: 2026-10-21  

---

## 1. Technical Context & Scope

- **App Framework**: React 18, Vite, TypeScript, ZMP SDK (`zmp-sdk`), ZaUI (`zmp-ui`), Tailwind CSS.
- **Routing**: `react-router-dom` v6 kết hợp `ZMPRouter` & `react-transition-group`.
- **State & Data Fetching**: `@tanstack/react-query` v5, Axios (`axiosInstance` với token Bearer), Custom hooks.
- **Form & Validation**: Zod, controlled React state, ZaUI DatePicker/Select/Modal.
- **Target Platform**: Zalo Super App (iOS & Android Webview container).

---

## 2. Research Items & Technical Decisions

### Decision 1: Cấu trúc Route & Trang Chi tiết Buổi họp (`MeetingDetailPage`)
- **Problem**: Hiện tại `CalendarPage` mở chi tiết meeting qua một `MeetingDetailModal` nhỏ. Giao diện này không đủ diện tích để hiển thị đầy đủ thông tin: Hero Card, Thống kê sĩ số, danh sách người tham dự kèm thao tác điểm danh và đặc biệt là hệ thống tab Đánh giá Trainee/Trainer.
- **Decision**: 
  - Khởi tạo route `/meetings/:id` dẫn đến `MeetingDetailPage.tsx`.
  - Khai báo path `PATHS.MEETING_DETAIL = '/meetings/:id'` trong [paths.ts](file:///Users/nguyenhuynh/Documents/dut-ai-manager/zalo-mini-app/dut-manager/src/constants/paths.ts).
  - Tích hợp điều hướng từ `MeetingCard` trên `CalendarPage` và các danh sách liên quan trực tiếp đến `/meetings/:id`.
- **Rationale**: Đảm bảo trải nghiệm trực quan, có back button rõ ràng trên Header ZaUI, tương đương 100% bản Web nhưng được tối ưu kích thước cảm ứng (touch targets > 44px).

### Decision 2: Kiến trúc Tab Đánh giá trên Mobile (Meeting Evaluation)
- **Problem**: Đánh giá buổi họp trên Web gồm 3 phần: Trainee Evaluation, Trainer Evaluation, và Meeting Overall Evaluation. Cần đưa lên Zalo Mini App sao cho gọn gàng, mượt mà.
- **Decision**:
  - Tận dụng component `Tabs` từ `zmp-ui` trên `MeetingDetailPage`:
    - Tab 1: **Người tham gia** (Danh sách thành viên, tag trạng thái, nút điểm danh, nút Host đổi trạng thái tham dự).
    - Tab 2: **Đánh giá Trainee** (Danh sách học viên cần đánh giá, modal chấm điểm theo tiêu chí có sẵn).
    - Tab 3: **Tổng kết buổi họp** (Overall evaluation: nhận xét chung, nội dung đạt được, số liệu sĩ số).
  - Tái sử dụng các endpoint API có sẵn trong backend:
    - `POST /meetings/{id}/evaluations/overall`
    - `GET /meetings/{id}/evaluations/overall`
    - `POST /meetings/{id}/evaluations/trainee`
    - `POST /meetings/{id}/evaluations/trainer`
    - `PUT /meetings/{id}/participants/{user_id}/status`
- **Rationale**: Tối ưu hiệu quả chấm điểm thực tế của Host/Trainer khi đang ngồi trực tiếp tại phòng họp di động.

### Decision 3: Chuẩn hóa Quản lý Đơn phép (Permissions Management)
- **Problem**: Cần đồng bộ giao diện hiển thị danh sách đơn phép giống Web (xem tất cả các đơn mà tài khoản có quyền xem, có bộ lọc đa năng: loại đơn, trạng thái, đơn của tôi). Đồng thời hoàn thiện luồng `CHANGE_MEETING` (Đổi ca sinh hoạt) với kiểm tra ghế trống.
- **Decision**:
  - Nâng cấp `PermissionsPage`:
    - Thêm bộ lọc: Dropdown / Tab chọn Loại đơn (`ALL`, `CHANGE_MEETING`, `ABSENCE`, `LATE`, `POSTPONE`, `OTHER`).
    - Thêm Switch/Filter: `Tất cả đơn` vs `Đơn của tôi`.
    - Thêm bộ lọc trạng thái (Chờ duyệt, Đã duyệt, Từ chối nếu có).
  - Trong `PermissionFormModal`:
    - Đơn `CHANGE_MEETING`: Fetch danh sách meeting tương lai, hiển thị số ghế trống `max_seat - (registered - absence)`. Cảnh báo trực quan nếu hết chỗ (`0 ghế trống`).
- **Rationale**: Thống nhất nghiệp vụ giữa Web và Mobile, giảm thiểu tối đa sai sót khi thành viên xin đổi ca.

---

## 3. Alternatives Considered

- **Giữ nguyên Modal trượt lên cho chi tiết meeting**: Bị bác bỏ vì modal trên di động khó chứa được dữ liệu bảng danh sách người tham dự dài (20-50 người) và form chấm điểm nhiều tiêu chí.
- **Tách riêng tính năng Đánh giá sang một trang khác**: Bị bác bỏ vì gây phân mảnh trải nghiệm; người dùng muốn xem buổi họp và chấm điểm ngay tại một nơi thông qua tabs.
