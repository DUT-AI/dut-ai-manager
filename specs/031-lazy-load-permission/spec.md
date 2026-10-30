# Feature Specification: Kịch bản A - Tối ưu danh sách PermissionRequest & Bổ sung API Detail

**Feature Branch**: `031-lazy-load-permission`  
**Created**: 2026-10-31  
**Status**: In Progress  

## 1. Problem Statement
Hiện tại API danh sách `GET /api/v1/permissions` đang eager-load (JOIN) toàn bộ các entity ORM nặng nề gồm `HomeworkModel`, `MeetingModel`, `OldMeetingModel` chỉ để lấy thông tin phụ. Việc này làm tăng độ trễ truy vấn gấp hơn 14 lần (~260ms so với ~18ms) và vi phạm ranh giới Aggregate Root trong DDD.
Người dùng đã chốt chọn **Kịch bản A**:
1. Danh sách `GET /api/v1/permissions` chỉ tải dữ liệu cơ bản (siêu nhẹ ~18ms), không JOIN `homework`, `meeting`, `old_meeting`.
2. Tạo mới API `GET /api/v1/permissions/{id}` trả về `PermissionRequestDetailResponse` (bao gồm đầy đủ quan hệ `homework`, `meeting`, `old_meeting`, `creator`, `updater`).
3. Khi người dùng mở Detail Drawer trên Frontend, Frontend sẽ gọi API `GET /api/v1/permissions/{id}` để nạp thông tin chi tiết.

## 2. Requirements & Acceptance Criteria
- **Backend**:
  - Trong `PermissionRequestRepository`: Loại bỏ toàn bộ `joinedload(ORMModel.homework)`, `joinedload(ORMModel.meeting)`, `joinedload(ORMModel.old_meeting)` khỏi các hàm lấy danh sách (`get_paged`, `get_by_date`, `get_by_month`, `get_by_user`). Chỉ giữ `joinedload(ORMModel.creator)`.
  - Thêm phương thức `get_detail_by_id(id: int) -> PermissionRequest | None` trong repository (hoặc trả về ORMModel/DetailEntity) có eager-load đầy đủ `creator`, `updater`, `homework`, `meeting`, `old_meeting`.
  - Tạo Use Case mới: `GetPermissionRequestDetailUseCase` trong `backend/app/permission_request/application/get_permission_request_detail_use_case.py`.
  - Thêm endpoint `GET /api/v1/permissions/{id}` trong `controller.py` với response model `ApiResponse[PermissionRequestDetailResponse]`.
  - Đăng ký Provider trong Dishka `providers.py`.
- **Frontend**:
  - Cập nhật service `permission.service.ts`: thêm hàm `getById(id: number)`.
  - Thêm hook `usePermissionDetail(id: number | null)` với React Query (`@tanstack/react-query`).
  - Trong `PermissionTable.tsx`: Cột "Mục tiêu" hiển thị nhẹ gọn theo ID (ví dụ: `#Bài tập {id}`, `#Buổi học {id}`).
  - Trong `PermissionDetailDrawer.tsx`: Khi `isOpen && item?.id`, gọi hook `usePermissionDetail` hiển thị spinner loading và render đầy đủ chi tiết khi có dữ liệu.
- **Testing**:
  - 100% backend unit test pass.
  - Frontend `npm run build` thành công không lỗi type.
