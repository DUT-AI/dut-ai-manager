# Feature Specification: Kiểm toán và Khắc phục Hiện tượng Lọc Nửa Vời trên Toàn bộ Dự án

**Feature Branch**: `032-audit-and-fix`  
**Created**: 2026-10-31  
**Status**: In Progress  

## 1. Problem Statement
Hiện tượng "Lọc nửa vời" (Client-side filtering on top of server-paginated data) xảy ra khi Backend phân trang theo trang (Page-based) nhưng Frontend lại lấy kết quả của trang đó rồi chạy hàm `.filter()` trên RAM của trình duyệt. Điều này dẫn đến việc:
- Trang 1 chỉ có 0-1 item thỏa mãn hoặc trống trơn.
- Người dùng phải lật sang các trang khác mới thấy được các bản ghi thỏa mãn điều kiện lọc.
- Tổng số lượng hiển thị trên thanh phân trang (`Pagination`) không phản ánh đúng số lượng bản ghi thực tế theo bộ lọc.

## 2. Kết quả kiểm toán toàn bộ codebase Frontend
Sau khi quét toàn bộ các trang (`frontend/src/features/**/pages/` và `components/`):
1. **UserManagementPage (`/dashboard/users`)**: Đã phát hiện và sửa xong (đã đẩy `role` và `status` xuống Server).
2. **PermissionManagementPage (`/dashboard/permissions`)**: ĐÃ ĐẨY SERVER 100% (`month`, `year`, `category`, `userId`, `page`, `pageSize` đều truyền vào `usePermissionRequests`).
3. **ViolationManagementPage (`/dashboard/violations`)**: ĐÃ ĐẨY SERVER 100% (gửi `month`, `year`, `userId`, `category`, `page`, `pageSize` về API).
4. **BonusPointManagementPage (`/dashboard/bonus-points`)**: ĐÃ ĐẨY SERVER 100% (gửi `month`, `year`, `userId`, `page`, `pageSize` về API).
5. **ExpenseManagementPage (`/dashboard/expenses`)**: ĐÃ ĐẨY SERVER 100% (gửi `month`, `year`, `category`, `page`, `pageSize` về API).
6. **AdminBillingPage (`/dashboard/billing`)**: ĐÃ ĐẨY SERVER 100% (gửi `month`, `year`, `status`, `page`, `pageSize` về API).
7. **HomeworkPage (`/dashboard/homeworks`)**:
   - `useHomeworks({ page, pageSize })` phân trang ở server.
   - Hiện tại trang quản lý bài tập không có bộ lọc bổ sung, chỉ có phân trang.
8. **MyHomeworkPage (`/dashboard/my-homeworks`)** (Cần kiểm tra kỹ):
   - Gọi `useMyHomeworks()` (hiện tại API `GET /homeworks/my-homeworks` trả về danh sách có phân trang nhưng query hook gọi `get_my_homeworks` không truyền page/pageSize, hoặc client lấy toàn bộ và lọc theo tab `all`, `unsubmitted`, `submitted`, `overdue`).
   - Cần đảm bảo nếu phân trang thì các tab phải đồng bộ hoặc API hỗ trợ filter.
9. **RobotActivityPage (`/dashboard/robot-activity`)**:
   - Trang này lấy danh sách lịch sử quẹt thẻ/điểm danh gần đây để robot hiển thị, quy mô nhỏ cục bộ.
10. **TeamManagementPage (`/dashboard/teams`)**:
    - Gọi `useTeams()` lấy toàn bộ danh sách team (thường ít, < 20 team) và tìm kiếm client-side. Không dùng Server Pagination nên không gặp lỗi văng trang.

## 3. Scope of Work
- Xác nhận và củng cố toàn bộ các màn hình có phân trang Server.
- Kiểm tra tính nhất quán giữa Server Pagination và Client Search/Filter.
- Đảm bảo khi người dùng thay đổi bất kỳ filter nào, `page` luôn được `resetPage()` về trang 1.
