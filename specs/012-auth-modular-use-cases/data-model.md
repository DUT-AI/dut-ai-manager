# Data Model & File Layout: Miền Xác Thực (Auth Application)

**Feature**: `012-auth-modular-use-cases` | **Date**: 2026-10-17

## 1. Cấu Trúc Module Use Cases Mới

```text
backend/app/auth/application/
├── __init__.py                               # Re-export các use case & DTOs
├── dtos.py                                   # Giữ nguyên
├── user_event_handler.py                     # Giữ nguyên
├── base_auth_use_case.py                     # BaseAuthUseCase (create_tokens, repos)
├── authenticate_use_case.py                  # AuthenticateUseCase
├── authenticate_zalo_phone_use_case.py       # AuthenticateZaloPhoneUseCase
├── refresh_token_use_case.py                 # RefreshTokenUseCase
├── get_me_use_case.py                        # GetMeUseCase
├── change_password_use_case.py               # ChangePasswordUseCase
├── create_account_use_case.py                # CreateAccountUseCase
└── forgot_password_use_case.py               # ForgotPasswordUseCase
```

## 2. Danh Sách Use Cases & Phụ Thuộc (Dependencies)

| Use Case Class | File Đích | Lớp Cha / Base | Phụ Thuộc (Injected Repos / Services) |
| :--- | :--- | :---: | :--- |
| `BaseAuthUseCase` | `base_auth_use_case.py` | - | `AccountRepository`, `UserRepository` |
| `AuthenticateUseCase` | `authenticate_use_case.py` | `BaseAuthUseCase` | `AccountRepository`, `UserRepository` |
| `AuthenticateZaloPhoneUseCase` | `authenticate_zalo_phone_use_case.py` | `BaseAuthUseCase` | `AccountRepository`, `UserRepository` |
| `RefreshTokenUseCase` | `refresh_token_use_case.py` | `BaseAuthUseCase` | `AccountRepository`, `UserRepository` |
| `GetMeUseCase` | `get_me_use_case.py` | - | `UserRepository` |
| `ChangePasswordUseCase` | `change_password_use_case.py` | `BaseAuthUseCase` | `AccountRepository`, `UserRepository` |
| `CreateAccountUseCase` | `create_account_use_case.py` | - | `AccountRepository`, `UserRepository` |
| `ForgotPasswordUseCase` | `forgot_password_use_case.py` | `BaseAuthUseCase` | `AccountRepository`, `UserRepository`, `EventBus` |
