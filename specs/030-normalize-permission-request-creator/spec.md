# Feature Specification: Normalize Permission Request Creator UserRef

**Feature Branch**: `030-normalize-permission-request-creator`  
**Created**: 2026-10-30  
**Status**: Draft  

## Problem Statement
Trong `PermissionRequest` (`backend/app/permission_request`), bảng database chỉ có `created_by` (người tạo đơn) và `updated_by`. Tuy nhiên, tầng Entity, Model, Schema và DTO trước đây kế thừa cấu trúc từ các domain `Violation`/`BonusPoint` nên sinh ra đồng thời 2 trường `owner: UserRef` và `creator: UserRef`. Cả hai trường này đều cùng trỏ vào `created_by`, gây trùng lặp, lãng phí tài nguyên mapping và làm rối rắm mô hình dữ liệu.

## Requirements
1. **Chuẩn hóa thông tin người tạo đơn**:
   - Thống nhất chỉ dùng 1 trường duy nhất đại diện cho thông tin người tạo đơn trong `PermissionRequest`: `creator: UserRef | None` (hoặc `owner: UserRef | None` nếu giữ tương thích FE, hoặc chuẩn hóa đồng bộ).
   - Kiểm tra xem nên chuẩn hóa thành `creator` hay giữ alias để FE không bị vỡ. Trên Frontend (`PermissionTable.tsx`, `PermissionMobileList.tsx`, `PermissionDetailDrawer.tsx`), các component đang đọc `record.owner?.name` và `record.owner?.avatar_url`.
   - Để sạch sẽ và an toàn tuyệt đối (không breaking change với Frontend):
     - Schema/DTO và Entity chuẩn hóa sử dụng trường `creator: UserRef | None`.
     - Đồng thời hỗ trợ `owner: UserRef | None` (computed property hoặc alias trỏ về `creator`) hoặc cập nhật cả FE & BE nhất quán để thống nhất tên gọi `creator`.
2. **Loại bỏ quan hệ kép trong ORM Model**:
   - `PermissionRequest` trong `infrastructure/model.py` hiện có cả:
     ```python
     user: Mapped["UserModel"] = relationship(foreign_keys="PermissionRequest.created_by", overlaps="creator")
     creator: Mapped["UserModel | None"] = relationship(foreign_keys="PermissionRequest.created_by", overlaps="user")
     ```
   - Xóa bỏ `user` relationship thừa và `overlaps="creator"` / `overlaps="user"`. Chỉ giữ một relationship duy nhất `creator` (hoặc `user` tùy quyết định đặt tên).
3. **Đảm bảo tính tương thích và kiểm thử**:
   - Tất cả unit test và API test liên quan phải pass 100%.
