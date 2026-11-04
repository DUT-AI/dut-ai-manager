# Quickstart: PWA Mobile Install Top Banner Validation Guide

Tài liệu này cung cấp các kịch bản kiểm thử trực quan và tự động nhằm xác thực tính năng **PWA Mobile Install Top Banner**.

---

## 1. Kịch bản 1: Kiểm thử trên Máy tính (Desktop PC / Laptop)

### Mục tiêu
Đảm bảo thanh banner **tuyệt đối không xuất hiện** trên trình duyệt máy tính thông thường.

### Các bước thực hiện
1. Khởi động môi trường phát triển:
   ```bash
   make frontend-dev
   ```
2. Mở trình duyệt Chrome / Safari trên máy tính ở cửa sổ thông thường (viewport > 1024px).
3. Truy cập địa chỉ `http://localhost:3000` (hoặc domain đang chạy).
4. Quan sát thanh trên cùng của trang web.

### Kết quả kỳ vọng
- Không xuất hiện bất kỳ thanh banner cài đặt PWA nào.
- Chỉ hiển thị thanh Push Notification Banner (nếu đã đăng nhập và chưa bật push) hoặc thanh Header bình thường.

---

## 2. Kịch bản 2: Giả lập Trình duyệt Điện thoại Android (Chrome Device Mode)

### Mục tiêu
Xác thực banner hiển thị ở trên cùng với nút "Cài đặt ngay" và kích hoạt hộp thoại cài đặt native của trình duyệt.

### Các bước thực hiện
1. Mở DevTools (`F12` hoặc `Cmd + Option + I`), bật chế độ Device Toolbar (`Cmd + Shift + M`).
2. Chọn thiết bị: **Pixel 7** hoặc **Samsung Galaxy S20**.
3. Tải lại trang (F5).

### Kết quả kỳ vọng
- Thanh banner xuất hiện ở trên cùng với nền xanh tím nhẹ:
  - Icon tải ứng dụng + câu thông điệp: *"Cài đặt DUT AI Manager về màn hình chính để mở nhanh và tiện lợi hơn."*
  - Nút *"Cài đặt ngay"* (hoặc *"Tải app"* trên màn hình hẹp).
  - Không có nút "Để sau".
- Khi bấm nút *"Cài đặt ngay"*:
  - Trên trình duyệt hỗ trợ `beforeinstallprompt`, hộp thoại cài đặt của trình duyệt xuất hiện.
  - Sau khi chọn cài đặt thành công, banner tự động biến mất.

---

## 3. Kịch bản 3: Giả lập Điện thoại iPhone (iOS Safari)

### Mục tiêu
Xác thực khi bấm "Cài đặt ngay" trên iOS, một modal hướng dẫn trực quan xuất hiện.

### Các bước thực hiện
1. Mở DevTools, bật Device Toolbar, chọn thiết bị **iPhone 14 Pro Max**.
2. Đổi User Agent trong tab Network Conditions sang Safari iPhone:
   `Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1`
3. Tải lại trang.
4. Chạm vào nút *"Cài đặt ngay"*.

### Kết quả kỳ vọng
- Modal hướng dẫn 2 bước xuất hiện rõ ràng:
  - Bước 1: Biểu tượng nút **Chia sẻ** (hộp có mũi tên hướng lên ở thanh dưới).
  - Bước 2: Chọn **"Thêm vào Màn hình chính" (Add to Home Screen)**.
- Bấm nút "Đã hiểu" để đóng modal. Banner trên cùng vẫn giữ nguyên vị trí cho đến khi app được mở từ màn hình chính.

---

## 4. Kịch bản 4: Kiểm thử Xếp tầng cùng Push Notification Banner

### Mục tiêu
Xác thực 2 thanh banner xếp tầng gọn gàng khi cả 2 cùng kích hoạt trên mobile.

### Các bước thực hiện
1. Đăng nhập tài khoản trên thiết bị di động giả lập (chưa cài app và chưa bật Web Push).
2. Quan sát phần đầu trang.

### Kết quả kỳ vọng
- Thanh PWA Install Banner nằm ở trên cùng.
- Thanh Push Notification Banner ("Bật thông báo đẩy...") nằm ngay bên dưới.
- Bố cục flex column không bị che khuất, không làm tràn trang (overflow ngang), text hiển thị rõ ràng.
