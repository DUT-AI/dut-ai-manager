# Feature Specification: Tối Ưu Hoá Độ Trễ Kết Nối Từ ESP32 Check-in Đến Backend (ESP32 Check-in Latency Optimization)

**Feature Branch**: `025-esp32-checkin-latency-optimization`  
**Created**: 2026-10-24  
**Status**: Ready for Review / Planning  
**Input**: Hiện tại khoảng thời gian từ lúc ESP32 quẹt thẻ bắt đầu gọi request đến Backend mất rất nhiều thời gian (thường từ 2s - 18s, đôi khi bị connection lost/timeout), trong khi sau khi Backend nhận được request thì xử lý rất nhanh (vài chục ms) và trả về ngay.

---

## 1. Phân Tích Hiện Trạng & Nguyên Nhân Gốc Rễ (Root Cause Analysis)

### Hiện tượng quan sát:
1. **Thời gian quẹt thẻ -> Backend nhận request**: Mất 2 đến 18 giây, đôi khi gặp lỗi `HTTP Response Code: -1 (connection refused)` hoặc `-5 (connection lost)`.
2. **Thời gian Backend xử lý**: Chỉ mất ~50 - 150ms (truy vấn user, check-in meeting, lấy TTS cached từ MinIO).
3. **Thời gian tải audio về ESP32**: Sau khi kết nối thành công thì tải về rất nhanh.

### Các nguyên nhân cốt lõi gây nghẽn tại bước kết nối:
1. **Thiết lập kết nối HTTPS / TLS mới trên mỗi lần quẹt thẻ (TLS Handshake Overhead)**:
   - Trong `main.ino`, mỗi lần quẹt thẻ lại khởi tạo mới một `WiFiClientSecure client` cục bộ.
   - ESP32 phải thực hiện đầy đủ chu trình: **DNS Lookup (`manage.dutai.io.vn`) -> TCP 3-Way Handshake -> TLS Handshake (mBedTLS key exchange, certificate parsing)**.
   - CPU ESP32 tính toán mã hoá tốn từ **1.5s - 3s** cho mỗi lần TLS Handshake qua Internet.
2. **DNS Resolution lặp lại nhiều lần**:
   - `http.begin(client, apiUrl)` giải quyết lại DNS của tên miền mỗi lần gọi. Khi mạng WiFi chập chờn hoặc DNS server phản hồi chậm, ESP32 bị treo mất 2-5s ở bước DNS.
3. **Vòng đời kết nối bị đóng hoàn toàn (`http.setReuse(false)`)**:
   - Hiện tại cấu hình `http.setReuse(false)` và `http.end()` hủy hoàn toàn socket sau mỗi request, buộc lần sau phải bắt tay lại từ đầu thay vì tái sử dụng kết nối HTTP Keep-Alive.
4. **Cloudflare Tunnel / Edge Timeout**:
   - URL `https://manage.dutai.io.vn` đi qua Cloudflare. Nếu kết nối từ ESP32 lên Cloudflare Edge bị drop gói SYN/ACK do cơ chế tiết kiệm năng lượng hoặc buffer nhỏ, Cloudflare sẽ reset connection hoặc chờ timeout 15s.

---

## 2. User Scenarios & Testing *(mandatory)*

### User Story 1 - Phản Hồi Tức Thì Khi Quẹt Thẻ (< 800ms) (Priority: P1)
Khi người dùng áp thẻ RFID vào đầu đọc, thiết bị gửi tín hiệu và nhận được phản hồi từ backend gần như tức thì, màn hình LCD hiển thị ngay kết quả và loa phát âm thanh trong vòng chưa tới 1 giây.

- **Why this priority**: Trải nghiệm người dùng tại quầy check-in yêu cầu tốc độ phản xạ tức thời. Độ trễ 3-18s làm người dùng tưởng thiết bị hỏng hoặc quẹt chưa ăn thẻ và quẹt lại nhiều lần.
- **Independent Test**: Dùng thẻ kiểm thử quẹt liên tiếp nhiều lần (cách nhau 5-10s). Đo thời gian từ lúc phát tiếng bíp đọc thẻ đến khi nhận HTTP Response Code 200 trên Serial Monitor. Thời gian trung bình phải đạt **< 800ms** (ở các lần quẹt tiếp theo khi đã có Keep-Alive).
- **Acceptance Scenarios**:
  1. **Given** ESP32 đã kết nối WiFi và sẵn sàng, **When** Người dùng quẹt thẻ lần đầu tiên, **Then** Thiết bị bắt tay kết nối và nhận phản hồi trong vòng tối đa **1.5s**.
  2. **Given** ESP32 đã hoàn thành 1 lần gọi trước đó, **When** Người dùng tiếp theo quẹt thẻ sau đó 5 giây, **Then** Thiết bị tái sử dụng kết nối (HTTP Keep-Alive), bỏ qua bước bắt tay TLS và nhận phản hồi trong vòng **< 500ms**.
  3. **Given** Mạng WiFi bị mất gói tin tạm thời, **When** Bắt tay TLS thất bại, **Then** ESP32 tự động retry thông minh trong vòng 200ms thay vì treo 18s hoặc báo lỗi ngay.

---

### User Story 2 - Ổn Định Kết Nối, Không Rớt Gói (Connection Lost / Refused) (Priority: P1)
Thiết bị check-in hoạt động liên tục 24/7 trong môi trường mạng thực tế (WiFi văn phòng/trường học) mà không bị rơi vào trạng thái `-1 connection refused` hay `-5 connection lost`.

- **Why this priority**: Thiết bị IoT đặt cố định tại cửa phòng họp phải hoạt động tin cậy, không được gián đoạn.
- **Independent Test**: Để ESP32 ở trạng thái nhàn rỗi (idle) 15 phút, sau đó quẹt thẻ. Thiết bị vẫn gửi được dữ liệu thành công mà không bị đứt kết nối ngầm.
- **Acceptance Scenarios**:
  1. **Given** ESP32 ở trạng thái chờ lâu, **When** Có thẻ quẹt, **Then** Nếu socket cũ bị server đóng do timeout, ESP32 phát hiện ngay và tự động mở lại socket mới mà không bị timeout 18s.
  2. **Given** Kết nối socket, **When** ESP32 hoạt động, **Then** WiFi modem sleep luôn ở trạng thái tắt (`WiFi.setSleep(false)` kiên định), không làm trễ gói tin ACK.

---

## 3. Yêu Cầu Kỹ Thuật Chi Tiết (Technical Requirements)

### 3.1. Cải tiến Firmware ESP32 (`checkin-esp32/main/main.ino`)
1. **HTTP Keep-Alive & Connection Pooling**:
   - Giữ đối tượng `WiFiClientSecure` và `HTTPClient` tái sử dụng (Persistent Connection).
   - Kích hoạt `http.setReuse(true)` để giữ socket TCP/TLS mở giữa các lần quẹt thẻ.
2. **Tối ưu hóa Buffer TLS mBedTLS**:
   - Sử dụng `client.setBufferSizes(512, 512)` cho request gửi đi và `4096` cho response, giúp giảm thiểu phân mảnh bộ nhớ RAM và tăng tốc mã hóa phần cứng.
3. **Cơ chế Keep-Alive Ping / Health Check**:
   - Nếu không có quẹt thẻ sau một khoảng thời gian (ví dụ 60s), gửi một gói tin heartbeat nhẹ để giữ kết nối Cloudflare tunnel luôn nóng (Warm-up Connection).
4. **Giảm Timeout Bắt Tay Hợp Lý (Fast-Fail)**:
   - Điều chỉnh timeout handshake từ `45s` xuống `5s - 8s`. Nếu sau 5s không bắt tay được thì ngắt ngay và thử lại ngay lập tức (Fast-fail & Quick Retry), loại bỏ hiện tượng treo 18 giây.

### 3.2. Cải tiến Phía Server / Backend
1. **Hỗ trợ HTTP Keep-Alive trên Endpoint**:
   - Đảm bảo FastAPI / Uvicorn server cấu hình `keep_alive_timeout` tối thiểu 65 giây (để tương thích với Cloudflare edge vốn giữ connection 60s).
   - Trả về header `Connection: keep-alive` và `Keep-Alive: timeout=60, max=1000`.

---

## 4. Kế Hoạch Xác Nhận & Nghiệm Thu (Verification Plan)

| Tiêu chí | Hiện tại | Mục tiêu sau tối ưu |
| :--- | :--- | :--- |
| **Độ trễ lần gọi đầu (Cold Start)** | 3.5s - 5.0s | **< 1.5s** |
| **Độ trễ các lần gọi tiếp theo (Warm/Keep-Alive)** | 2.5s - 18.0s | **< 500ms - 800ms** |
| **Tỷ lệ lỗi Connection lost (-5) / Refused (-1)** | Thỉnh thoảng xuất hiện khi idle | **0% (Tự động phục hồi ngầm)** |
| **Thời gian timeout khi mất mạng** | 18s - 45s | **Tối đa 5s rồi phản hồi ngay** |
