# Quickstart & Verification Guide: Tự Động Làm Mới Token Khi Hết Hạn

**Feature**: `049-auto-refresh-token`
**Date**: 2026-11-04

Tài liệu này hướng dẫn cách kiểm thử và xác minh tính năng tự động làm mới token ngầm (Silent Token Refresh) trên môi trường phát triển và kiểm thử tự động.

---

## 1. Điều kiện Tiên quyết (Prerequisites)

- Môi trường Backend đang hoạt động: Python 3.12+ với `pytest` và các phụ thuộc dự án (`uv sync` hoặc `poetry install`).
- Môi trường Frontend: Node.js 20+ với `npm run build` và Vite dev server.

---

## 2. Kịch bản Kiểm thử Tự động (Automated Tests)

### 2.1. Backend Unit Tests cho `/auth/refresh`
Chạy bộ kiểm thử kiểm tra tính hợp lệ và xử lý mã lỗi HTTP 401 khi refresh token thiếu hoặc không hợp lệ:

```bash
pytest backend/tests/unit/test_auth_refresh.py -v
```

**Kỳ vọng:**
- Trường hợp refresh token hợp lệ: Trả về HTTP 200, cấp cặp `access_token` và `refresh_token` mới trong cookie và response.
- Trường hợp refresh token không tồn tại trong cookie và body: Ném `BadRequestException(status_code=401)` trả về HTTP 401.
- Trường hợp refresh token hết hạn hoặc giả mạo: Ném `BadRequestException(status_code=401)` trả về HTTP 401.

### 2.2. Frontend Build & Static Analysis
Xác minh không có lỗi kiểu dữ liệu TypeScript và build thành công:

```bash
cd frontend && npm run build
```

---

## 3. Kịch bản Xác minh Thủ công trên Giao diện (Manual E2E Verification)

### Kịch bản 1: Tự động gia hạn ngầm khi gọi API (Silent Refresh on 401)
1. Đăng nhập vào hệ thống bằng tài khoản bất kỳ tại `/login`.
2. Mở DevTools (F12) -> tab **Application** -> **Cookies**.
3. Sửa hoặc xóa giá trị cookie `access_token` (giả lập access token hết hạn) nhưng **giữ nguyên** cookie `refresh_token`.
4. Trên giao diện, bấm vào một tính năng (ví dụ: chuyển tab cuộc họp hoặc bấm xem chi tiết).
5. **Quan sát tab Network:**
   - Yêu cầu ban đầu nhận mã `401 Unauthorized`.
   - Một yêu cầu `POST /api/v1/auth/refresh` được tự động gửi ngầm.
   - Yêu cầu ban đầu được tự động phát lại (replay) và hoàn thành với mã `200 OK`.
   - Giao diện người dùng hiển thị dữ liệu bình thường, hoàn toàn không bị văng ra màn hình đăng nhập.

### Kịch bản 2: Tải lại trang tại route gốc `/` khi Access Token hết hạn
1. Đăng nhập thành công, sau đó truy cập `http://localhost:5173/`.
2. Xóa cookie `access_token`, giữ lại `refresh_token`.
3. Nhấn `F5` tải lại trang.
4. **Quan sát:**
   - Hệ thống tự động kích hoạt làm mới token ngầm khi gọi `/auth/me`.
   - Người dùng được chuyển thẳng vào `/dashboard` với đầy đủ thông tin tài khoản, không bị chuyển hướng sang `/login`.

### Kịch bản 3: Hết hạn toàn bộ (Cả Refresh Token đều hết hạn)
1. Đăng nhập vào hệ thống.
2. Xóa sạch cả hai cookie `access_token` và `refresh_token`.
3. Nhấn vào một tính năng trên trang.
4. **Quan sát:**
   - Yêu cầu `/auth/refresh` trả về lỗi 401.
   - Thông báo "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại." hiển thị đúng 1 lần duy nhất.
   - Hệ thống chuyển hướng mượt mà về trang `/login`.
