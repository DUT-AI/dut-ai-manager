# Feature Specification: Tách Biệt Use Cases Đơn Nhiệm Miền Xác Thực (Auth Modular Use Cases)

**Feature Branch**: `012-auth-modular-use-cases`

**Created**: 2026-10-17

**Status**: Draft

**Input**: User description: "Tôi muốn tách các use case này thành các file con, không cần tương thích ngược như module meeting"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Tách Biệt Toàn Bộ Các Use Case Xác Thực Thành Các File Đơn Nhiệm (Priority: P1)

Nhà phát triển và hệ thống có thể dễ dàng định vị, kiểm thử và mở rộng từng nghiệp vụ xác thực (Đăng nhập Email/Password, Đăng nhập SĐT Zalo, Làm mới Token, Lấy thông tin bản thân, Đổi mật khẩu, Tạo tài khoản và Quên mật khẩu) trong một tệp nguồn riêng biệt thay vì tập trung trong một tệp nguyên khối `use_cases.py`, tuân thủ nghiêm ngặt Điều lệ Dự án (Constitution Principle VII).

**Why this priority**: Đây là yêu cầu cốt lõi nhằm giải quyết tình trạng vi phạm nguyên tắc Single Responsibility (SRP) ở tầng Application, chuẩn hóa cấu trúc thư mục tương tự như miền `meeting` và `bonus_point`.

**Independent Test**: Mỗi use case (`authenticate_use_case.py`, `authenticate_zalo_phone_use_case.py`, `refresh_token_use_case.py`, `get_me_use_case.py`, `change_password_use_case.py`, `create_account_use_case.py`, `forgot_password_use_case.py`) cùng logic dùng chung `base_auth_use_case.py` có thể được import, khởi tạo và kiểm thử độc lập mà không cần nạp toàn bộ các use case còn lại.

**Acceptance Scenarios**:

1. **Given** một yêu cầu đăng nhập bằng email & password, **When** hệ thống thực thi, **Then** nghiệp vụ được đảm nhiệm bởi `AuthenticateUseCase` trong tệp `authenticate_use_case.py`.
2. **Given** một yêu cầu đăng nhập bằng số điện thoại Zalo, **When** hệ thống thực thi, **Then** nghiệp vụ được đảm nhiệm bởi `AuthenticateZaloPhoneUseCase` trong `authenticate_zalo_phone_use_case.py`.
3. **Given** các yêu cầu cấp lại token, lấy thông tin cá nhân, đổi mật khẩu, đăng ký tài khoản hoặc quên mật khẩu, **When** hệ thống xử lý, **Then** mỗi nghiệp vụ được phụ trách bởi chính xác một tệp tương ứng (`refresh_token_use_case.py`, `get_me_use_case.py`, `change_password_use_case.py`, `create_account_use_case.py`, `forgot_password_use_case.py`).
4. **Given** lớp cơ sở hỗ trợ sinh token `BaseAuthUseCase`, **When** các use case đăng nhập/xác thực kế thừa, **Then** lớp này nằm độc lập trong `base_auth_use_case.py`.

---

### User Story 2 - Xóa Bỏ Hoàn Toàn Tệp Monolithic và Chuẩn Hóa Import Qua Gói Application (Priority: P2)

Gói ứng dụng `app.auth.application` xuất khẩu (re-export) toàn bộ các use case và lớp base thông qua `__init__.py` với danh sách `__all__` minh bạch theo đúng chuẩn Constitution Principle VII. Tệp nguyên khối cũ `use_cases.py` bị xóa bỏ hoàn toàn (không duy trì file shim tương thích ngược). Toàn bộ các import trong `backend/app/auth/providers.py` và `backend/app/auth/controller.py` được chuyển đổi sang import trực tiếp từ `app.auth.application`.

**Why this priority**: Loại bỏ hoàn toàn nợ kỹ thuật (technical debt), chuẩn hóa clean architecture đồng nhất với miền `meeting`.

**Independent Test**: Chạy `grep` toàn bộ codebase xác nhận không còn bất kỳ dòng nào tham chiếu tới `app.auth.application.use_cases`, tệp `use_cases.py` không còn tồn tại trên ổ đĩa, và toàn bộ hệ thống khởi động, chạy test thành công 100%.

**Acceptance Scenarios**:

1. **Given** tệp `use_cases.py` bị xóa bỏ hoàn toàn, **When** khởi động ứng dụng hoặc chạy test, **Then** `providers.py` và `controller.py` nạp use cases thành công từ `app.auth.application` mà không gặp bất kỳ lỗi `ImportError` nào.

---

### Edge Cases

- **Kế thừa BaseAuthUseCase**: Đảm bảo `base_auth_use_case.py` chỉ chứa logic chia sẻ (`create_tokens`, inject `AccountRepository`, `UserRepository`) và các use case kế thừa import sạch sẽ mà không gây tuần hoàn phụ thuộc (Circular Dependency).
- **Dishka Container Resolution**: Các class use case giữ nguyên 100% signature hàm `__init__` và `execute` để không làm thay đổi hay gián đoạn cơ chế Dependency Injection của Dishka Provider.
- **Sự kiện ForgotPasswordRequested**: Đảm bảo `ForgotPasswordUseCase` vẫn phát sự kiện thông qua `EventBus` như cũ với đầy đủ dữ liệu.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Hệ thống PHẢI chia tách 7 use case và 1 base class trong `backend/app/auth/application/use_cases.py` thành 8 tệp nguồn riêng biệt theo quy ước `*_use_case.py`:
  - `base_auth_use_case.py` (`BaseAuthUseCase`)
  - `authenticate_use_case.py` (`AuthenticateUseCase`)
  - `authenticate_zalo_phone_use_case.py` (`AuthenticateZaloPhoneUseCase`)
  - `refresh_token_use_case.py` (`RefreshTokenUseCase`)
  - `get_me_use_case.py` (`GetMeUseCase`)
  - `change_password_use_case.py` (`ChangePasswordUseCase`)
  - `create_account_use_case.py` (`CreateAccountUseCase`)
  - `forgot_password_use_case.py` (`ForgotPasswordUseCase`)
- **FR-002**: Tệp `backend/app/auth/application/__init__.py` PHẢI re-export toàn bộ 7 use case cùng `BaseAuthUseCase`, DTOs, UserAccountHandler và định nghĩa danh sách `__all__` đầy đủ theo Điều lệ Dự án (Constitution Principle VII).
- **FR-003**: Hệ thống PHẢI xóa bỏ hoàn toàn tệp `backend/app/auth/application/use_cases.py`, không duy trì file shim tương thích ngược.
- **FR-004**: Tệp Dishka Provider (`backend/app/auth/providers.py`) và Controller (`backend/app/auth/controller.py`) PHẢI được cập nhật import trực tiếp từ `app.auth.application`.
- **FR-005**: Toàn bộ logic nghiệp vụ, xác thực JWT, hash mật khẩu và phát sự kiện miền (`ForgotPasswordRequested`) PHẢI được bảo toàn nguyên vẹn 100%.

### Key Entities

- **Account**: Thực thể tài khoản đăng nhập (email, password_hash, user_id, zalo_user_id, status).
- **UserEntity**: Thực thể thông tin người dùng và quyền hạn/vai trò.
- **Domain Event**: `ForgotPasswordRequested`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% các use case trong miền auth được đặt trong các tệp riêng biệt theo quy ước `*_use_case.py`.
- **SC-002**: Tệp `use_cases.py` trong `backend/app/auth/application` được loại bỏ hoàn toàn (0 file nguyên khối).
- **SC-003**: 0 lỗi `ImportError` trên toàn bộ hệ thống backend khi chuyển đổi cấu trúc file.
- **SC-004**: Đạt tỷ lệ vượt qua 100% (Zero Regression) trên toàn bộ các bài kiểm thử liên quan đến auth (`pytest backend/tests/api/test_auth_api.py`, v.v.).

## Assumptions

- Các DTO (`dtos.py`), Entity (`Account`), Repository (`AccountRepository`, `UserRepository`) giữ nguyên vị trí và interface hiện có.
- Cơ chế giải quyết dependency injection của Dishka container hoạt động dựa trên type annotations của từng use case class.
