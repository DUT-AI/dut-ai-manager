# Feature Specification: Hệ Thống Thông Báo (In-App Notification Center & Push Notification) Trên Zalo Mini App

**Feature Directory**: `specs/021-zalo-mini-app-notification-system`  
**Created**: 2026-10-21  
**Status**: Specified / Clarified  
**Input**: "Hiện tại trên web có 1 hệ thống notification in app, tôi muốn ở zalo mini app cũng có và có thể hiển thị thông báo trên điện thoại của người dùng như 1 app native thì có được ko?"

---

## 1. Phân Tích Kỹ Thuật & Giải Đáp Về Khả Năng Push & Chi Phí Zalo

### 1.1. Về cơ chế Push Notification ra điện thoại như Native App
- **Đặc thù Zalo Mini App**: Zalo Mini App hoạt động bên trong webview của ứng dụng Zalo mẹ. Khi người dùng tắt Mini App, Mini App **không thể** tự duy trì một background service độc lập để bắn Local Push Notification từ client như ứng dụng native (.apk / .ipa).
- **Cơ chế Push qua Zalo Platform**: Để thông báo xuất hiện trên màn hình khóa/thanh thông báo của điện thoại người dùng (kèm chuông/rung), hệ thống phải gửi qua **Zalo Official Account (OA)** hoặc **Zalo Notification Service (ZNS)** từ Backend. Khi người dùng chạm vào thông báo trên điện thoại, Zalo sẽ kích hoạt mở Mini App và điều hướng đến màn hình chi tiết tương ứng.

### 1.2. Giải đáp chi tiết câu hỏi: "Zalo OA với ZNS đều phải tốn phí đúng không?"
1. **ZNS (Zalo Notification Service - Gửi theo số điện thoại)**:
   - **CÓ TỐN PHÍ 100%**: Chi phí khoảng **200đ – 500đ / tin nhắn** tùy loại template (Ưu tiên, Tiêu chuẩn, OTP).
   - Yêu cầu tạo tài khoản Zalo Cloud Account (ZCA), nạp tiền trả trước và phải đăng ký duyệt template mẫu tin với Zalo.
2. **Zalo Official Account (OA)**:
   - **Gói Miễn phí**: Có thể tạo OA miễn phí, nhưng bị **giới hạn rất khắt khe** theo chính sách mới của Zalo (không thể chủ động push tin nhắn thông báo đến người theo dõi nếu người dùng không tương tác/nhắn tin với OA trong 48h gần nhất).
   - **Gói Trả phí (Doanh nghiệp/Nâng cao)**: Phí duy trì từ **55.000đ – 399.000đ/tháng**, yêu cầu OA xác thực tích vàng (giấy tờ pháp nhân tổ chức/trường học) mới được cấp hạn mức gửi tin nhắn Transaction CSKH qua Open API.
3. **In-App Notification Center (Trung tâm thông báo bên trong Mini App)**:
   - **HOÀN TOÀN MIỄN PHÍ 100% (KHÔNG TỐN MỘT XU)**:
   - Sử dụng hạ tầng Backend hiện hữu (`/api/v1/notifications`), lưu trữ trên PostgreSQL.
   - Hiển thị badge số lượng chưa đọc trên Header, trang danh sách thông báo phân loại đẹp mắt, cập nhật thời gian thực khi mở app.
4. **Giải pháp thay thế Push ra điện thoại MIỄN PHÍ 100%**:
   - Tích hợp thêm **Telegram Bot Notification** (đã có kiến trúc tại `specs/005-telegram-bot-notification`): Thành viên liên kết tài khoản Telegram với DUT Manager, bot tự động bắn push notification lên điện thoại kèm nút "Mở Zalo Mini App".

---

## 2. Clarifications (Làm Rõ Yêu Cầu)

### Session 2026-10-21
- **Q1**: Zalo OA với ZNS có tốn phí không và có push ra ngoài như native app được không?
  - **A**: 
    - Có, ZNS tốn phí trên từng tin nhắn, còn Zalo OA cần gói trả phí duy trì hàng tháng và xác thực tích vàng để gửi tin nhắn chủ động.
    - Cả hai đều hiển thị được Push Notification ra màn hình khóa điện thoại thông qua app Zalo.
- **Q2**: Chiến lược triển khai tính năng Notification trên Zalo Mini App?
  - **A**: Ưu tiên triển khai hoàn thiện **In-App Notification Center (0 đồng)** đồng bộ 100% với Web và Backend `/api/v1/notifications`. Cấu trúc hệ thống ở Backend theo dạng Adapter đa kênh để sẵn sàng bật/tắt Zalo OA/ZNS hoặc Telegram Bot khi cần mà không phải sửa giao diện Mini App.

---

## 3. User Scenarios & Testing

### User Story 1 - Xem trung tâm thông báo & đếm số lượng chưa đọc (Priority: P1)
Người dùng mở Zalo Mini App, thấy biểu tượng Chuông ở Header có badge đỏ đếm số thông báo mới chưa đọc. Khi bấm vào chuông, người dùng được chuyển tới trang Trung tâm Thông báo (`/notifications`).

**Acceptance Criteria**:
1. Header hiển thị biểu tượng Chuông thông báo với số lượng unread badge (lấy từ `/api/v1/notifications/unread-count`). Nếu = 0 thì ẩn badge đỏ.
2. Danh sách thông báo hiển thị theo thứ tự mới nhất, phân loại rõ ràng (Bài tập `HOMEWORK`, Lịch sinh hoạt `MEETING`, Trực nhật `DUTY`, Đơn phép `PERMISSION`, Hệ thống `SYSTEM`).
3. Thông báo chưa đọc có nền nổi bật và dấu chấm xanh; thông báo đã đọc có màu trầm hơn.

---

### User Story 2 - Thao tác tương tác thông báo (Đọc, Đọc tất cả, Lọc) (Priority: P2)
Người dùng lọc thông báo theo danh mục, bấm "Đánh dấu tất cả đã đọc" hoặc xóa/đọc từng thông báo.

**Acceptance Criteria**:
1. Bấm nút "Đã đọc tất cả" (`POST /api/v1/notifications/read-all`) -> Cập nhật toàn bộ trạng thái thành đã đọc, badge chuông về 0 ngay lập tức.
2. Bộ lọc tab: Tất cả / Chưa đọc / Bài tập / Lịch họp / Đơn từ.
3. Khi bấm vào 1 thông báo cụ thể:
   - Gọi API `PATCH /api/v1/notifications/{id}/read` để đánh dấu đã đọc.
   - Nếu thông báo có liên kết thực thể (ví dụ `meeting_id` hoặc `homework_id`), ứng dụng tự động điều hướng sang trang chi tiết tương ứng (`/meetings/{id}` hoặc `/homeworks/{id}`).

---

### User Story 3 - Thông báo dạng In-App Banner khi đang mở ứng dụng (Priority: P3)
Khi người dùng đang mở Zalo Mini App và có sự kiện mới (hoặc định kỳ poll), một banner thông báo nổi (Toast/Snackbar) trượt nhẹ từ trên xuống giúp người dùng nhận biết ngay lập tức.

**Acceptance Criteria**:
1. Hiển thị tiêu đề và nội dung ngắn gọn.
2. Cho phép chạm vào banner để mở ngay màn hình chi tiết sự kiện.

---

## 4. API Endpoints Tích Hợp (Đã Có Sẵn Ở Backend)

1. `GET /api/v1/notifications/my?page=1&page_size=20&category={cat}&is_read={bool}`: Lấy danh sách thông báo của tôi (hỗ trợ phân trang và lọc).
2. `GET /api/v1/notifications/unread-count`: Đếm tổng số thông báo chưa đọc.
3. `PATCH /api/v1/notifications/{id}/read`: Đánh dấu đã đọc 1 thông báo.
4. `POST /api/v1/notifications/read-all`: Đánh dấu tất cả thông báo là đã đọc.
5. `DELETE /api/v1/notifications/{id}`: Xóa thông báo khỏi danh sách.

---

## 5. Non-Functional & UI/UX Standards
- Giao diện thiết kế theo chuẩn Mobile-First của Zalo Mini App (bo tròn góc 2xl, bảng màu hiện đại, responsive, không giật lag).
- Empty state thân thiện khi chưa có thông báo nào.
- Hỗ trợ pull-to-refresh hoặc auto refetch thông báo khi quay lại tab.
