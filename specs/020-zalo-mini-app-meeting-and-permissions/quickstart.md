# Quickstart Guide: Đồng Bộ Lịch Meeting & Quản Lý Đơn Phép Trên Zalo Mini App

## 1. Môi trường kiểm thử & Khởi động
Vào thư mục Zalo Mini App:
```bash
cd zalo-mini-app/dut-manager
npm install
npm run dev
```

Mở trình duyệt hoặc Zalo Mini App Simulator theo URL nội bộ để kiểm thử.

---

## 2. Kịch bản kiểm thử End-to-End

### Kịch bản 1: Điều hướng & Xem Chi tiết Buổi họp (`MeetingDetailPage`)
1. Truy cập tab **Lịch** (`/calendar`).
2. Chọn một buổi sinh hoạt trên danh sách tuần/tháng.
3. Nhấp vào buổi sinh hoạt -> Ứng dụng chuyển sang `/meetings/:id`.
4. Xác nhận giao diện hiển thị:
   - Header có nút quay lại (`<`).
   - Hero Card tóm tắt: Tiêu đề, thời gian, phòng họp, link online.
   - Hàng chỉ số sĩ số: Tổng tham gia, Có mặt, Vắng, Đi trễ.
   - Tab 1: **Người tham gia** liệt kê đầy đủ danh sách thành viên và trạng thái.
   - Nút **Điểm danh**: Bấm tải ảnh/chụp ảnh để gửi điểm danh.

### Kịch bản 2: Host chấm điểm Đánh giá Trainee
1. Đăng nhập với tài khoản có quyền Host/Admin.
2. Mở `/meetings/:id` của một buổi họp có bật đánh giá.
3. Chuyển sang Tab 2: **Đánh giá Trainee**.
4. Chọn một Trainee -> Mở popup chấm điểm.
5. Nhập điểm các tiêu chí và lưu -> Điểm và trạng thái đánh giá cập nhật ngay lập tức.

### Kịch bản 3: Quản lý Đơn xin phép & Tạo đơn Đổi ca (`CHANGE_MEETING`)
1. Mở trang **Đơn xin phép** (`/permissions`).
2. Kiểm tra danh sách hiển thị tất cả các đơn của hệ thống (nếu là Admin) hoặc đơn cá nhân (nếu là Member).
3. Thử chuyển đổi các tab lọc danh mục: `Vắng`, `Trễ`, `Hoãn bài tập`, `Đổi buổi sinh hoạt`.
4. Bấm **Tạo đơn mới** -> Chọn loại **Đổi buổi sinh hoạt**.
5. Chọn ca hiện tại và ca đích -> Hệ thống hiển thị số ghế trống.
6. Bấm gửi đơn -> Đơn được tạo thành công và tự động duyệt nếu còn chỗ.
