# Tasks: Tái cấu trúc Định danh Xác thực (Auth Principal Refactor)

**Input**: Design documents from `specs/010-auth-principal-refactor/` (plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md)

**Prerequisites**: plan.md (completed), spec.md (completed), data-model.md (completed), contracts/ (completed)

**Tests**: Bao gồm các unit test và integration test xác thực luồng định danh và phân quyền mới.

**Organization**: Các đầu việc được cấu trúc theo User Story để có thể triển khai, kiểm thử độc lập và bàn giao tăng dần.

## Format: `- [ ] [ID] [P?] [Story?] Description with file path`

- **[P]**: Có thể thực hiện song song (khác file, không phụ thuộc task đang chờ)
- **[Story]**: Đánh dấu User Story tương ứng (`[US1]`, `[US2]`, `[US3]`)

---

## Phase 1: Setup (Chuẩn bị Môi trường & Hạ tầng)

**Purpose**: Chuẩn bị tệp định danh cốt lõi và kiểm tra môi trường chạy kiểm thử

- [x] T001 Khởi tạo tệp mô hình định danh mới tại `backend/app/core/principal.py`
- [x] T002 [P] Khởi tạo tệp kiểm thử unit test mới tại `backend/tests/unit/core/test_auth_principal.py`
- [x] T003 [P] Khởi tạo tệp kiểm thử dependencies xác thực tại `backend/tests/unit/core/test_auth_deps.py`

---

## Phase 2: Foundational (Nền tảng Cốt lõi)

**Purpose**: Xây dựng cấu trúc dữ liệu `AuthPrincipal` và an toàn hóa ngữ cảnh kiểm toán trước khi tích hợp vào router

**⚠️ CRITICAL**: Các User Story bên dưới phụ thuộc vào mô hình nền tảng hoàn thành ở giai đoạn này

- [x] T004 Định nghĩa Enum `PrincipalType` (`USER = "USER"`, `API_KEY = "API_KEY"`) tại `backend/app/core/principal.py`
- [x] T005 Triển khai Pydantic model `AuthPrincipal` tại `backend/app/core/principal.py` với các trường: `actor_id: int | None = None`, `actor_type: PrincipalType`, `name: str`, `email: str | None = None`, `role_names: list[str] = Field(default_factory=list)`, `permissions: set[str] = Field(default_factory=set)`
- [x] T006 Triển khai các phương thức nghiệp vụ trong `AuthPrincipal`: `has_permission(permission_name: str) -> bool` (tự động thông qua nếu role có `ADMIN`), `is_user -> bool`, `is_api_key -> bool`, và `user_id -> int` (ném `BadRequestException(403)` nếu là API Key) tại `backend/app/core/principal.py`
- [x] T007 Cập nhật ngữ cảnh kiểm toán tại `backend/app/core/context.py` để hỗ trợ `set_current_user_id(user_id: int | None)` an toàn, cho phép nhận `None` đối với API Key để tránh lưu ID giả `0` vào cơ sở dữ liệu

**Checkpoint**: Nền tảng `AuthPrincipal` đã sẵn sàng, các luồng User Story có thể bắt đầu tích hợp.

---

## Phase 3: User Story 1 - Tách biệt Định danh Xác thực và Thực thể Người dùng (Priority: P1) 🎯 MVP

**Goal**: Triển khai hàm giải mã token/API Key mới trả về `AuthPrincipal` thay vì `UserEntity`, chấm dứt việc tạo `UserEntity(id=0)` cho API Key.

**Independent Test**: Gửi request mang API Key hợp lệ và JWT token hợp lệ: hệ thống phân định chính xác loại `API_KEY` và `USER`, không tạo bất kỳ `UserEntity(id=0)` nào.

### Tests for User Story 1 ⚠️
- [x] T008 [P] [US1] Viết unit tests kiểm tra khởi tạo và hành vi của `AuthPrincipal` (kiểm tra `has_permission`, `is_user`, `is_api_key`, `user_id` property khi là User và khi là API Key) trong `backend/tests/unit/core/test_auth_principal.py`
- [x] T009 [P] [US1] Viết unit tests kiểm thử hàm giải mã API Key và JWT token trả về đúng `AuthPrincipal` trong `backend/tests/unit/core/test_auth_deps.py`

### Implementation for User Story 1
- [x] T010 [US1] Tái cấu trúc logic API Key trong hàm xác thực tại `backend/app/core/deps.py`: loại bỏ hoàn toàn việc khởi tạo `UserEntity(id=0, ...)` và thay thế bằng `AuthPrincipal(actor_id=matched_key.id, actor_type=PrincipalType.API_KEY, name=f"System: {matched_key.name}", role_names=role_names, permissions=perms)`
- [x] T011 [US1] Đặt `set_current_user_id(None)` khi xác thực thành công qua API Key tại `backend/app/core/deps.py`
- [x] T012 [US1] Cập nhật định nghĩa alias `CurrentUser = Annotated[AuthPrincipal, Depends(get_current_principal)]` tại `backend/app/core/deps.py`

**Checkpoint**: User Story 1 hoàn thành độc lập. Luồng xác thực API Key đã hoàn toàn sạch sẽ, không còn đối tượng `id=0` ảo.

---

## Phase 4: User Story 2 - Kiểm tra Quyền hạn Nhanh từ Ngữ cảnh Xác thực (Priority: P2)

**Goal**: Tối ưu hóa xác thực JWT người dùng: nạp trực tiếp vai trò và quyền hạn từ JWT claims vào `AuthPrincipal`, không truy vấn cơ sở dữ liệu dư thừa khi chỉ cần kiểm tra phân quyền RBAC.

**Independent Test**: Gửi request với JWT chứa quyền hợp lệ đến endpoint có `hasPermission(...)`: quyền hạn được phê duyệt trực tiếp mà không kích hoạt câu lệnh `SELECT` bản ghi người dùng trong cơ sở dữ liệu.

### Tests for User Story 2 ⚠️
- [x] T013 [P] [US2] Viết integration test kiểm thử `PermissionChecker` với `AuthPrincipal` (quyền hợp lệ, thiếu quyền bị 403, vai trò ADMIN tự động bypass) trong `backend/tests/unit/core/test_auth_deps.py`

### Implementation for User Story 2
- [x] T014 [US2] Tối ưu hóa nhánh xử lý JWT Access Token trong `get_current_principal` tại `backend/app/core/deps.py`: khởi tạo `AuthPrincipal(actor_id=payload.sub, actor_type=PrincipalType.USER, name=payload.name, email=payload.email, role_names=payload.roles, permissions=set(payload.permissions))` trực tiếp từ `AccessTokenPayload`
- [x] T015 [US2] Cập nhật `PermissionChecker.__call__` tại `backend/app/core/deps.py` để nhận `current_user: CurrentUser` (AuthPrincipal) và kiểm tra quyền qua `current_user.has_permission(self.permission)`
- [x] T016 [US2] Kiểm tra và cập nhật hàm tiện ích `hasPermission(permission)` tại `backend/app/core/deps.py` để bảo đảm tương thích liền mạch

**Checkpoint**: User Story 2 hoàn thành. Hệ thống kiểm tra quyền nhanh chóng qua JWT claims, giảm tải tối đa cho cơ sở dữ liệu.

---

## Phase 5: User Story 3 - Bảo toàn Tương thích cho Nghiệp vụ Hồ sơ Cá nhân (Priority: P3)

**Goal**: Cung cấp dependency `CurrentUserEntity` cho các endpoint thực sự cần đọc dữ liệu chi tiết của `UserEntity` (Zalo, Discord, phone), tự động từ chối nếu bị gọi bởi API Key. Đồng thời cập nhật các hàm kiểm tra đặc thù (`hasTeamLeaderAccess`, `onlyEditOrDeleteYourself`).

**Independent Test**: Endpoint cần `UserEntity` hoạt động bình thường với người dùng thật, nhưng trả về 403 Forbidden nếu gọi bằng API Key.

### Tests for User Story 3 ⚠️
- [x] T017 [P] [US3] Viết unit tests kiểm thử `get_current_user_entity`: thành công khi là User và ném lỗi 403 khi là API Key trong `backend/tests/unit/core/test_auth_deps.py`

### Implementation for User Story 3
- [x] T018 [US3] Triển khai dependency `get_current_user_entity` tại `backend/app/core/deps.py`: kiểm tra `principal.is_user`, lấy `UserEntity` từ `UserRepository` và định nghĩa alias `CurrentUserEntity = Annotated[UserEntity, Depends(get_current_user_entity)]`
- [x] T019 [US3] Tinh chỉnh hàm `hasTeamLeaderAccess` và `onlyEditOrDeleteYourself` tại `backend/app/core/deps.py` để tương thích an toàn với `AuthPrincipal` (kiểm tra `current_user.is_user` trước khi so sánh `target_user_id`)
- [x] T020 [US3] Kiểm tra điểm cuối `get_my_homeworks` tại `backend/app/homework/controller.py` đảm bảo sử dụng `current_user.user_id` an toàn, từ chối API Key nếu không có ngữ cảnh người dùng

**Checkpoint**: Cả 3 User Stories hoàn tất, toàn bộ hệ thống đạt tính tương thích ngược và bảo mật cao.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Đảm bảo toàn bộ dự án sạch sẽ, không có lỗi linter/type-check và bộ test suite toàn diện vượt qua thành công.

- [x] T021 [P] Kiểm tra xuất nhập khẩu (re-exports) tại `backend/app/core/__init__.py` để các module bên ngoài có thể import `AuthPrincipal`, `CurrentUser`, `CurrentUserEntity` thuận tiện
- [x] T022 Chạy toàn bộ test suite `pytest backend/tests/` để xác nhận Zero Regression
- [x] T023 Chạy các kịch bản kiểm thử mẫu theo hướng dẫn `specs/010-auth-principal-refactor/quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies
- **Phase 1 (Setup)**: Hoàn thành.
- **Phase 2 (Foundational)**: Hoàn thành.
- **Phase 3 (User Story 1 - P1 🎯 MVP)**: Hoàn thành.
- **Phase 4 (User Story 2 - P2)**: Hoàn thành.
- **Phase 5 (User Story 3 - P3)**: Hoàn thành.
- **Phase 6 (Polish)**: Hoàn thành.

### Parallel Opportunities
- Các task test và model đã hoàn tất và được xác thực tự động qua `pytest`.

---

## Implementation Strategy

### MVP First (User Story 1 Only)
1. Hoàn thành Phase 1 (Setup) và Phase 2 (Foundational).
2. Triển khai Phase 3 (User Story 1): Thay thế việc fake `UserEntity(id=0)` bằng `AuthPrincipal` cho API Key.
3. Chạy kiểm thử xác nhận API Key hoạt động sạch sẽ không còn `id=0`.

### Incremental Delivery
1. Bước 1: Setup + Foundational -> Khởi tạo `AuthPrincipal`.
2. Bước 2: User Story 1 (MVP) -> Chuẩn hóa API Key không còn `id=0`.
3. Bước 3: User Story 2 -> Tối ưu hóa phân quyền JWT nhanh không query DB.
4. Bước 4: User Story 3 -> Hoàn thiện `CurrentUserEntity` và an toàn hóa các hàm helper.
5. Bước 5: Polish -> Chạy toàn bộ `pytest` xác nhận Zero Regression.
