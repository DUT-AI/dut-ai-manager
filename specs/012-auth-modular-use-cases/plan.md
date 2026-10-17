# Implementation Plan: Tách Biệt Use Cases Đơn Nhiệm Miền Xác Thực (Auth Modular Use Cases)

**Branch**: `012-auth-modular-use-cases` | **Date**: 2026-10-17 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/012-auth-modular-use-cases/spec.md)

**Input**: Đặc tả tính năng từ `/specs/012-auth-modular-use-cases/spec.md` theo yêu cầu refactor tách tệp `use_cases.py` thành các tệp riêng lẻ như module `meeting` và xóa bỏ hoàn toàn tệp `use_cases.py`.

---

## 1. Summary

Thực hiện chia tách tệp nguyên khối `backend/app/auth/application/use_cases.py` (chứa 7 use cases và 1 base class) thành 8 tệp đơn nhiệm riêng biệt tuân thủ tuyệt đối Điều lệ Dự án (**Constitution Principle VII: Single-Responsibility Use Cases**). Tệp nguyên khối `use_cases.py` sẽ bị xóa bỏ hoàn toàn không giữ file shim tương thích ngược theo chỉ thị người dùng. Tất cả 7 use case và `BaseAuthUseCase` sẽ được re-export minh bạch qua `backend/app/auth/application/__init__.py` thông qua biến `__all__`. Đồng thời, chuẩn hóa các câu lệnh import tại tất cả các vị trí phụ thuộc (`providers.py`, `controller.py`) sang import trực tiếp từ `app.auth.application`.

---

## 2. Technical Context

- **Language/Version**: Python 3.12 (môi trường ảo `backend/.venv`)
- **Primary Dependencies**: FastAPI, Dishka (Dependency Injection), SQLAlchemy 2.0, Pydantic V2, PyJWT / Passlib
- **Storage**: PostgreSQL (SQLAlchemy ORM với `AccountModel`, `UserModel`)
- **Testing**: PyTest (`pytest backend/tests/api/test_auth_api.py`)
- **Target Platform**: Linux Server / Docker Backend Service
- **Project Type**: Web Service API (Backend Clean Architecture)
- **Performance Goals**: Zero latency overhead (việc tách module cấp độ tệp tin chỉ ảnh hưởng tĩnh tại thời điểm nạp module)
- **Constraints**: 
  - Không thay đổi logic nghiệp vụ xác thực, hash password, sinh token hoặc phát sự kiện miền (`ForgotPasswordRequested`).
  - Xóa bỏ triệt để `use_cases.py`, không để lại dead code hoặc circular imports.
- **Scale/Scope**: 7 use case classes + 1 base class, 1 `__init__.py`, 2 call sites (`providers.py`, `controller.py`), 0 test regressions.

---

## 3. Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Trạng thái | Ghi chú |
| :--- | :--- | :---: | :--- |
| **Principle I: Clean Architecture & Practical DDD** | Application layer chỉ điều phối logic miền, repository và phát domain event. | **PASS** | Bảo toàn ranh giới giữa Domain, Application và Infrastructure. |
| **Principle II: Dependency Injection with Dishka** | Tất cả use cases được đăng ký qua `providers.py` và giải quyết qua container. | **PASS** | Tên lớp và method signature giữ nguyên 100%, Dishka resolve hoàn toàn tương thích. |
| **Principle III: Unified UTC+7 Timezone** | Thời gian hết hạn của token giữ nguyên theo cấu hình hệ thống. | **PASS** | Sử dụng `settings.ACCESS_TOKEN_EXPIRE_MINUTES`. |
| **Principle IV: Event-Driven Decoupling** | Giữ nguyên việc publish domain event `ForgotPasswordRequested`. | **PASS** | Sự kiện được xuất bản qua `EventBus` như thiết kế cũ. |
| **Principle V: API Backward Compatibility** | Giữ nguyên API contract và Response models. | **PASS** | Không ảnh hưởng đến các router HTTP hay schema JSON. |
| **Principle VII: Single-Responsibility Use Cases** | Mỗi use case PHẢI nằm trong 1 tệp `*_use_case.py` riêng biệt; `__init__.py` xuất khẩu qua `__all__`; cấm gom vào `use_cases.py`. | **PASS** | Đây chính là mục tiêu tiên quyết của kế hoạch này. |

---

## 4. Project Structure

### Documentation (this feature)

```text
specs/012-auth-modular-use-cases/
├── plan.md              # Kế hoạch triển khai kiến trúc (tệp này)
├── research.md          # Kết quả khảo sát mã nguồn & phương án refactor
├── data-model.md        # Cấu trúc tệp thư mục & phân loại phụ thuộc use cases
├── quickstart.md        # Hướng dẫn kiểm thử tự động & xác nhận xóa file
└── contracts/
    └── auth-use-cases.contract.md # Hợp đồng giao tiếp & chữ ký phương thức
```

### Source Code Layout

```text
backend/app/
└── auth/
    ├── application/
    │   ├── __init__.py                               # Re-export các use case & DTOs qua __all__
    │   ├── dtos.py                                   # Giữ nguyên
    │   ├── user_event_handler.py                     # Giữ nguyên
    │   ├── base_auth_use_case.py                     # [MỚI] Tách BaseAuthUseCase
    │   ├── authenticate_use_case.py                  # [MỚI] Tách AuthenticateUseCase
    │   ├── authenticate_zalo_phone_use_case.py       # [MỚI] Tách AuthenticateZaloPhoneUseCase
    │   ├── refresh_token_use_case.py                 # [MỚI] Tách RefreshTokenUseCase
    │   ├── get_me_use_case.py                        # [MỚI] Tách GetMeUseCase
    │   ├── change_password_use_case.py               # [MỚI] Tách ChangePasswordUseCase
    │   ├── create_account_use_case.py                # [MỚI] Tách CreateAccountUseCase
    │   ├── forgot_password_use_case.py               # [MỚI] Tách ForgotPasswordUseCase
    │   └── use_cases.py                              # [XÓA BỎ HOÀN TOÀN]
    ├── controller.py                                 # Cập nhật import từ app.auth.application
    └── providers.py                                  # Cập nhật import từ app.auth.application
```

---

## 5. Implementation Phases

### Phase 1: Chuẩn bị & Trích xuất các Use Case Đơn Nhiệm
1. Tạo 8 tệp mới trong thư mục `backend/app/auth/application/`:
   - `base_auth_use_case.py`
   - `authenticate_use_case.py`
   - `authenticate_zalo_phone_use_case.py`
   - `refresh_token_use_case.py`
   - `get_me_use_case.py`
   - `change_password_use_case.py`
   - `create_account_use_case.py`
   - `forgot_password_use_case.py`
2. Đưa đúng các imports cần thiết vào từng file (Repository, EventBus, Entities, DTOs, Password Utils).

### Phase 2: Cấu hình Re-export tại `__init__.py`
1. Tạo / Cập nhật `backend/app/auth/application/__init__.py`:
   - Import 7 lớp use case + `BaseAuthUseCase` từ các module con tương ứng.
   - Import `UserAccountHandler` và các DTOs.
   - Định nghĩa `__all__` đầy đủ.

### Phase 3: Chuẩn hóa Điểm Gọi (Call Sites) & Xóa Bỏ File Cũ
1. Cập nhật import trong `backend/app/auth/providers.py` -> `from app.auth.application import (...)`.
2. Cập nhật import trong `backend/app/auth/controller.py` -> `from app.auth.application import (...)`.
3. Xóa vĩnh viễn tệp `backend/app/auth/application/use_cases.py`.

### Phase 4: Kiểm thử Xác minh & Đảm bảo Zero Regression
1. Kiểm tra tĩnh: Xác nhận không còn chuỗi `app.auth.application.use_cases` trong toàn bộ repo (`grep_search`).
2. Chạy kiểm thử pytest:
   - `backend/.venv/bin/pytest backend/tests/api/test_auth_api.py -v`

---

## 6. Complexity Tracking

> Không có vi phạm Constitution nào cần biện minh. Toàn bộ thiết kế đưa codebase về đúng chuẩn Constitution Principle VII.

