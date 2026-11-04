---
description: "Danh sách công việc triển khai tính năng Tự Động Làm Mới Token Khi Hết Hạn"
---

# Tasks: Tự Động Làm Mới Token Khi Hết Hạn (Auto Refresh Token)

**Input**: Tài liệu thiết kế từ `specs/049-auto-refresh-token/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md), [data-model.md](./data-model.md), [contracts/auth-refresh-contract.yaml](./contracts/auth-refresh-contract.yaml)

## Format: `[ID] [P?] [Story] Description with file path`

- **[P]**: Có thể thực hiện song song (các tệp độc lập, không phụ thuộc vào task đang chờ)
- **[Story]**: Nhãn User Story tương ứng (`[US1]`, `[US2]`, `[US3]`) theo `spec.md`
- Mỗi mô tả công việc bắt buộc phải kèm đường dẫn tệp cụ thể

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Chuẩn bị cấu trúc tệp kiểm thử và khai báo kiểu dữ liệu cho cơ chế refresh token

- [x] T001 [P] Chuẩn bị môi trường kiểm thử Backend và tạo file test fixture trong backend/tests/unit/test_auth_refresh.py
- [x] T002 [P] Khai báo kiểu dữ liệu cho hàng đợi refresh và đối tượng callback trong frontend/src/services/axiosInstance.ts

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Chuẩn hóa phản hồi HTTP status code của API `/auth/refresh` trên Backend để Frontend có thể phát hiện và bắt lỗi chính xác

**⚠️ CRITICAL**: Các công việc trong giai đoạn này bắt buộc phải hoàn thành trước khi triển khai các User Story trên Frontend

- [x] T003 Chuẩn hóa mã lỗi xác thực trong backend/app/auth/application/refresh_token_use_case.py (ném `BadRequestException(status_code=401, message="Invalid or expired refresh token")` thay vì 400)
- [x] T004 Cập nhật xử lý thiếu token trong backend/app/auth/controller.py (ném `BadRequestException(status_code=401, message="Refresh token is missing")` khi không có token trong cookie hoặc body)
- [x] T005 Viết unit tests kiểm thử endpoint `/auth/refresh` trong backend/tests/unit/test_auth_refresh.py để bảo đảm phản hồi trả về đúng mã HTTP 200 khi thành công và 401 khi token thiếu/không hợp lệ

**Checkpoint**: Nền tảng Backend hoàn tất — endpoint `/auth/refresh` đảm bảo chuẩn HTTP 401. Có thể bắt đầu triển khai Frontend.

---

## Phase 3: User Story 1 - Tự động gia hạn phiên ngầm khi Access Token hết hạn (Priority: P1) 🎯 MVP

**Goal**: Khi `access_token` hết hạn trong lúc người dùng thao tác hoặc khi người dùng tải lại trang tại route gốc `/`, hệ thống tự động gọi ngầm `/auth/refresh` và retry lại request ban đầu thành công mà không ngắt quãng trải nghiệm.

**Independent Test**: Làm cho `access_token` hết hạn hoặc sửa cookie `access_token`, thực hiện một thao tác gửi yêu cầu dữ liệu (hoặc tải lại trang tại `/`). Yêu cầu được tự động refresh và hoàn thành thành công với dữ liệu, không bị đẩy ra `/login`.

### Implementation for User Story 1

- [x] T006 [US1] Loại bỏ điều kiện chặn refresh sai lầm `window.location.pathname === '/'` trong frontend/src/services/axiosInstance.ts để cho phép refresh tại route gốc và mọi dashboard route
- [x] T007 [US1] Thêm kiểm tra phòng ngừa vòng lặp vô tận (Infinite Loop Prevention) cho các auth endpoints (`/auth/refresh`, `/auth/login`) trong frontend/src/services/axiosInstance.ts
- [x] T008 [US1] Triển khai cơ chế tự động gửi `POST /auth/refresh` với `withCredentials: true` và phát lại request ban đầu (`axiosInstance(originalRequest)`) khi có lỗi 401 trong frontend/src/services/axiosInstance.ts
- [x] T009 [US1] Xác minh kịch bản khởi tạo trang và gọi `authService.getMe()` trong frontend/src/features/auth/context/AuthContext.tsx hoạt động liền mạch khi access token hết hạn mà refresh token còn hiệu lực

**Checkpoint**: User Story 1 hoàn thành độc lập — người dùng không còn bị văng ra trang đăng nhập khi access token hết hạn lúc thao tác đơn lẻ hoặc tải lại trang.

---

## Phase 4: User Story 2 - Xếp hàng và thực thi lại các yêu cầu đồng thời (Priority: P2)

**Goal**: Khi nhiều request cùng phát sinh đồng thời lúc token vừa hết hạn, chỉ có duy nhất 1 request `/auth/refresh` được gửi đi; các request còn lại được giữ trong hàng đợi Promise `failedQueue` và tự động replay sau khi refresh thành công.

**Independent Test**: Gửi đồng thời 5-10 requests khi access token hết hạn; kiểm tra tab Network chỉ có đúng 1 request `/auth/refresh` được phát đi; toàn bộ các request đều nhận được kết quả dữ liệu hợp lệ.

### Implementation for User Story 2

- [x] T010 [US2] Hoàn thiện cơ chế khóa phiên `isRefreshing` và hàng đợi Promise `failedQueue` trong frontend/src/services/axiosInstance.ts để chặn các request tiếp theo không kích hoạt refresh trùng lặp
- [x] T011 [US2] Triển khai hàm `processQueue` giải phóng toàn bộ các request đang chờ trong `failedQueue` sau khi nhận được token mới trong frontend/src/services/axiosInstance.ts
- [x] T012 [US2] Đảm bảo cờ `originalRequest._retry = true` được gán chính xác trên từng request được phát lại để tránh retry nhiều lần trong frontend/src/services/axiosInstance.ts

**Checkpoint**: Cả User Story 1 và User Story 2 đều hoạt động ổn định — hỗ trợ tải các màn hình phức tạp có nhiều widget gọi API song song mà không xung đột phiên.

---

## Phase 5: User Story 3 - Xử lý đăng xuất an toàn khi Refresh Token hết hạn hoặc không hợp lệ (Priority: P3)

**Goal**: Khi `refresh_token` cũng đã hết hạn hoặc bị thu hồi từ máy chủ, hệ thống dọn dẹp hàng đợi, xóa trạng thái xác thực trong `AuthContext`, hiển thị thông báo "Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại" đúng 1 lần (singleton debounce), và điều hướng an toàn về `/login`.

**Independent Test**: Xóa/làm hỏng cả access token và refresh token. Thực hiện request. Hệ thống nhận 401 trên `/auth/refresh`, huỷ hàng đợi, hiển thị popup thông báo 1 lần duy nhất và điều hướng về `/login`.

### Implementation for User Story 3

- [x] T013 [US3] Triển khai xử lý lỗi thất bại của `/auth/refresh` trong khối `catch` để từ chối toàn bộ hàng đợi `failedQueue` (`processQueue(refreshError, null)`) trong frontend/src/services/axiosInstance.ts
- [x] T014 [US3] Thêm cờ singleton `isRedirectingToLogin` chống trùng lặp thông báo đăng xuất trong frontend/src/services/axiosInstance.ts để chỉ hiển thị đúng 1 popup thông báo khi có nhiều request đồng thời thất bại
- [x] T015 [US3] Đảm bảo dọn dẹp trạng thái người dùng trong frontend/src/features/auth/context/AuthContext.tsx trước khi chuyển hướng về `/login`

**Checkpoint**: Cả 3 User Story đều hoạt động hoàn chỉnh — xử lý phiên đăng nhập trơn tru và an toàn trong mọi tình huống.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Kiểm thử tự động toàn diện và kiểm tra tính tương thích mã nguồn

- [x] T016 [P] Kiểm tra và xác nhận toàn bộ unit test backend với lệnh `pytest backend/tests/unit/test_auth_refresh.py -v`
- [x] T017 [P] Kiểm tra biên dịch TypeScript toàn bộ ứng dụng frontend với `cd frontend && npm run build`
- [x] T018 Thực hiện xác minh theo kịch bản kiểm thử thủ công trong specs/049-auto-refresh-token/quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Không có phụ thuộc — có thể bắt đầu ngay lập tức.
- **Foundational (Phase 2)**: Phụ thuộc vào Setup — **Chặn** toàn bộ các User Story cho đến khi Backend chuẩn hóa mã HTTP 401.
- **User Stories (Phase 3+)**: Phụ thuộc vào Foundational hoàn thành:
  - **US1 (P1)**: Thực hiện đầu tiên để đạt mục tiêu MVP (Silent Refresh đơn lẻ & fix bug route `/`).
  - **US2 (P2)**: Phụ thuộc vào cơ chế refresh của US1, mở rộng xử lý concurrency với hàng đợi.
  - **US3 (P3)**: Phụ thuộc vào US1/US2, hoàn thiện xử lý lỗi khi refresh thất bại và điều hướng an toàn.
- **Polish (Phase 6)**: Phụ thuộc vào cả 3 User Story đã hoàn tất.

### Parallel Opportunities

- T001 và T002 có thể thực hiện song song (Backend test fixture vs Frontend types).
- T016 và T017 có thể chạy song song (Backend pytest vs Frontend npm run build).

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Hoàn thành Phase 1 (Setup) và Phase 2 (Foundational Backend 401 alignment).
2. Hoàn thành Phase 3 (User Story 1: xóa bỏ điều kiện chặn `/`, xử lý silent refresh).
3. **Xác minh MVP**: Kiểm tra tính năng làm mới token ngầm hoạt động cho request đơn lẻ và khi F5 tải lại trang.

### Incremental Delivery

1. Setup + Foundational -> Nền tảng Backend sẵn sàng.
2. Thêm User Story 1 -> Silent refresh cơ bản hoạt động (MVP).
3. Thêm User Story 2 -> Hỗ trợ gọi nhiều API đồng thời không xung đột.
4. Thêm User Story 3 -> Đăng xuất an toàn và trải nghiệm người dùng sạch sẽ khi hết hạn hoàn toàn.
5. Polish -> Chạy test tự động và build production.
