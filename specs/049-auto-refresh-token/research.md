# Research & Architectural Decisions: Tự Động Làm Mới Token Khi Hết Hạn (Auto Refresh Token)

**Feature**: `049-auto-refresh-token`
**Date**: 2026-11-04
**Author**: Antigravity Orchestrator

## 1. Bối cảnh & Vấn đề Cốt lõi (Problem Statement)

Hiện tại trong hệ thống `dut-ai-manager`, người dùng gặp hiện tượng bị tự động đăng xuất phi lý khi `access_token` hết hạn. Qua phân tích chi tiết mã nguồn hiện trạng:
1. **Lỗi điều kiện chặn refresh tại route gốc (`axiosInstance.ts`)**:
   ```typescript
   if (window.location.pathname === '/login' || window.location.pathname === '/') {
       return Promise.reject(error);
   }
   ```
   Khi người dùng tải trang lần đầu tại `http://.../`, `window.location.pathname` là `'/'`. Hook khởi tạo `AuthContext` gọi `/auth/me`. Nếu `access_token` vừa hết hạn, interceptor từ chối xử lý refresh vì đang ở `'/'`, dẫn đến `authService.getMe()` thất bại và người dùng bị ép chuyển hướng về `/login`.
2. **Lỗi xử lý phản hồi Backend không đạt chuẩn HTTP (`axiosInstance.ts` & `controller.py`)**:
   Khi `refresh_token` bị thiếu trong request, controller trả về:
   ```python
   return ApiResponse.error(message="Refresh token is missing")
   ```
   Do không đặt `status_code` trên đối tượng response hay ném exception, FastAPI trả về mã HTTP `200 OK` kèm `{ is_success: false, ... }`. Axios coi đây là thành công, khối `if (response.data.is_success)` bị bỏ qua, `failedQueue` không được giải phóng và bị treo vĩnh viễn (memory leak / promise hang).
3. **Thiếu cơ chế lọc endpoint nhạy cảm (Loop Prevention)**:
   Nếu chính yêu cầu `/auth/refresh` bị lỗi 401 hoặc 400, cần dừng ngay lập tức thay vì thử lại chính nó.
4. **Trải nghiệm người dùng khi hết hạn hoàn toàn**:
   Khi cả `refresh_token` hết hạn hoặc bị thu hồi, nhiều request đồng thời gửi lên sẽ kích hoạt nhiều thông báo lỗi lặp đi lặp lại. Cần cơ chế debounce/singleton notification.

---

## 2. Các Quyết định Kỹ thuật (Decisions & Rationales)

### Quyết định 1: Kiến trúc Reactive 401 Interceptor với Hàng đợi Promise Queue

- **Lựa chọn**: Sử dụng cơ chế Interceptor bất đồng bộ bắt lỗi HTTP `401 Unauthorized` trên instance Axios duy nhất (`axiosInstance`), kết hợp cờ `isRefreshing` và hàng đợi `failedQueue` dạng Promise callback.
- **Lý do**:
  - Tối ưu tài nguyên mạng: Chỉ gửi duy nhất 1 request `/auth/refresh` khi access token hết hạn, bất kể có bao nhiêu request đồng thời (ví dụ tải trang dashboard có 6 widgets).
  - Trong suốt với giao diện (Transparent to UI): Các React Query hooks hay service calls không cần biết đến sự tồn tại của việc làm mới token; chúng chỉ nhận dữ liệu sau khi request được retry thành công.
- **Giải pháp thay thế đã đánh giá**:
  - *Proactive Timer (Refresh định kỳ bằng setTimeout/setInterval)*: Bị từ chối vì không đáng tin cậy khi người dùng khóa máy, chuyển tab, hoặc tab rơi vào chế độ ngủ (background throttle); gây lãng phí tài nguyên máy chủ khi người dùng không thao tác.

### Quyết định 2: Chuẩn hóa HTTP Status Code trên Backend `/auth/refresh`

- **Lựa chọn**: Trong `backend/app/auth/controller.py` và `refresh_token_use_case.py`, khi `refresh_token` bị thiếu, không hợp lệ hoặc hết hạn, hệ thống PHẢI ném `BadRequestException(status_code=401, message=...)` thay vì trả về `ApiResponse.error(...)` với HTTP 200.
- **Lý do**:
  - Tuân thủ RESTful HTTP Standards: Lỗi xác thực phiên phải có mã HTTP `401 Unauthorized`.
  - Giúp Axios interceptor kích hoạt đúng khối `catch (refreshError)` và giải phóng `failedQueue` dứt khoát.
  - Tuân thủ Nguyên tắc XIV của Hiến pháp dự án (*Fail-Fast Parameter Contracts*).

### Quyết định 3: Sửa đổi Điều kiện Chặn Refresh trên Frontend

- **Lựa chọn**: 
  - Chỉ bỏ qua việc refresh nếu:
    1. Yêu cầu đang gọi là endpoint đăng nhập (`/auth/login`), làm mới phiên (`/auth/refresh`), hoặc đổi mật khẩu.
    2. URL của trình duyệt hiện tại đang là `/login`.
  - **Loại bỏ hoàn toàn** điều kiện `window.location.pathname === '/'`.
- **Lý do**: Route `'/'` là điểm điều hướng mặc định chuyển đến `/dashboard`. Khi mở ứng dụng tại `'/'`, hệ thống cần được phép làm mới token ngầm để duy trì đăng nhập của người dùng.

### Quyết định 4: Cơ chế Singleton Thông báo và Điều hướng khi Phiên Hết Hạn

- **Lựa chọn**: Tạo cờ `isRedirectingToLogin` và chỉ kích hoạt `message.error("Phiên đăng nhập đã hết hạn...")` một lần duy nhất. Hủy toàn bộ hàng đợi `failedQueue` bằng `Promise.reject` để các component ngừng chờ đợi, sau đó chuyển hướng về `/login`.
- **Lý do**: Tránh tình trạng hiển thị dồn dập 5-10 thông báo lỗi giống nhau trên màn hình khi nhiều request cùng thất bại lúc token hết hạn hoàn toàn.

---

## 3. Ma trận So sánh & Đánh giá Rủi ro (Risk Matrix)

| Kịch bản Rủi ro | Mức độ | Biện pháp Phòng ngừa |
|---|---|---|
| Request `/auth/refresh` bị lỗi 401 gây vòng lặp vô tận | Nghiêm trọng | Đánh dấu `_retry = true` và kiểm tra `originalRequest.url.includes('/auth/refresh')` trước khi thử refresh. |
| Nhiều tab trình duyệt gửi request cùng lúc khi token hết hạn | Trung bình | Vì hệ thống dùng HttpOnly cookie chia sẻ chung giữa các tab trên cùng origin, tab đầu tiên refresh thành công sẽ cập nhật cookie cho toàn bộ các tab khác. |
| Mạng bị gián đoạn (Network Offline / 502 Bad Gateway) trong lúc refresh | Thấp | Kiểm tra nếu lỗi không phải 401 (ví dụ `ERR_NETWORK` hoặc 500) thì không ép đăng xuất, mà giữ nguyên phiên để người dùng thử lại kết nối. |
