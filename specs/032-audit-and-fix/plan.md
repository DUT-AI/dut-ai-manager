# Implementation Plan: Kiểm toán và Đảm bảo Đồng bộ Bộ lọc - Phân trang Server

- **Branch**: `032-audit-and-fix`
- **Spec**: `specs/032-audit-and-fix/spec.md`

## 1. Kết quả kiểm tra đối soát chi tiết (Audit Matrix)

| Màn hình (Feature Page) | Phân trang (Pagination) | Bộ lọc (Filters) | Trạng thái (Status) | Hành động (Action) |
|---|---|---|---|---|
| **UserManagementPage** | Server (`useTablePagination`) | `keyword`, `role`, `status` | ✅ Đã chuẩn hóa | Đã đẩy xuống Backend query SQL thành công |
| **PermissionManagementPage** | Server (`useTablePagination`) | `month`, `year`, `category`, `userId` | ✅ Chuẩn | Toàn bộ filter được gửi qua URL params xuống Repository |
| **ViolationManagementPage** | Server (`useTablePagination`) | `month`, `year`, `userId`, `category` | ✅ Chuẩn | Toàn bộ filter được query trực tiếp từ Backend SQL |
| **BonusPointManagementPage** | Server (`useTablePagination`) | `month`, `year`, `userId` | ✅ Chuẩn | Toàn bộ filter được query trực tiếp từ Backend SQL |
| **ExpenseManagementPage** | Server (`useTablePagination`) | `month`, `year`, `category` | ✅ Chuẩn | Toàn bộ filter được query trực tiếp từ Backend SQL |
| **AdminBillingPage** | Server (`useTablePagination`) | `month`, `year`, `status` | ✅ Chuẩn | Filter gửi xuống backend billing repository |
| **TrashViolationPage** | Server (`useTablePagination`) | Phân trang thùng rác | ✅ Chuẩn | Không có bộ lọc con cục bộ |
| **TrashPermissionRequestPage** | Server (`useTablePagination`) | Phân trang thùng rác | ✅ Chuẩn | Không có bộ lọc con cục bộ |
| **TrashBonusPointPage** | Server (`useTablePagination`) | Phân trang thùng rác | ✅ Chuẩn | Không có bộ lọc con cục bộ |
| **HomeworkPage** | Server (`useTablePagination`) | Phân trang bài tập | ✅ Chuẩn | Không có bộ lọc con |
| **MyHomeworkPage** | Client-side Tabs | Tab `all`, `unsubmitted`, `submitted`, `overdue` | ⚠️ Cần kiểm tra | Không có server pagination, lấy toàn bộ bài tập của user và lọc client-side (Hợp lý vì số bài tập của 1 cá nhân ít) |
| **TeamManagementPage** | Client-side search | Tìm kiếm theo tên team | ✅ Chuẩn | Không có phân trang server (danh sách team nhỏ < 20) |

## 2. Kết luận kiểm toán
Chỉ có duy nhất trang **`UserManagementPage`** trước đó bị lỗi kiến trúc "lọc nửa vời" do `role` và `status` chưa được Backend hỗ trợ trong API `GET /api/v1/users` và đã được chúng ta sửa xong hoàn hảo. Tất cả các trang quản lý nghiệp vụ cốt lõi khác (`Permissions`, `Violations`, `BonusPoints`, `Expenses`, `Billing`) đều đã được thiết kế chuẩn chỉnh từ trước với việc gửi 100% tham số lọc xuống cơ sở dữ liệu.
