# Kế hoạch Triển khai: Tái cấu trúc Định danh Xác thực (Implementation Plan)

**Branch**: `010-auth-principal-refactor` | **Date**: 2026-10-17 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/010-auth-principal-refactor/spec.md)

**Input**: Feature specification from `/specs/010-auth-principal-refactor/spec.md`

## Summary

Tách biệt hoàn toàn mô hình định danh xác thực (`AuthPrincipal`) ra khỏi thực thể nghiệp vụ cơ sở dữ liệu (`UserEntity`). Điều này loại bỏ triệt để code smell giả lập người dùng ảo (`id=0`) khi gọi bằng API Key, khắc phục rủi ro xung đột toàn vẹn khóa ngoại trong cơ sở dữ liệu, tối ưu hóa tốc độ kiểm tra quyền hạn (RBAC) trên các endpoint dùng JWT mà không cần truy vấn bảng người dùng dư thừa, đồng thời bảo toàn tính tương thích ngược cho toàn bộ các controller hiện tại.

## Technical Context

**Language/Version**: Python 3.11+

**Primary Dependencies**: FastAPI, Pydantic V2, PyJWT, SQLAlchemy 2.0, Passlib (Bcrypt)

**Storage**: PostgreSQL (SQLAlchemy ORM models: `RoleApiKey`, `Role`, `User`, `Permission`)

**Testing**: pytest (Unit & Integration tests)

**Target Platform**: Linux Server / Docker Container / macOS dev

**Project Type**: Backend Web Service (FastAPI REST API)

**Performance Goals**: Giảm 100% các truy vấn SQL đọc bảng `users` ở tầng xác thực đối với các endpoint chỉ yêu cầu kiểm tra quyền hạn thông qua JWT claims; thời gian giải mã và xác thực quyền đạt < 2ms/request.

**Constraints**: Tương thích ngược 100% với chữ ký hiện tại của các bộ điều khiển sử dụng `CurrentUser`, `hasPermission`, `PermissionChecker`; không làm gãy các luồng nghiệp vụ hiện có.

**Scale/Scope**: Áp dụng xuyên suốt toàn bộ hệ thống API backend (`backend/app/core/deps.py` và các controller liên quan).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **I. Clean Architecture & Practical DDD Boundaries (MUST)**: Đạt. Tách biệt rõ ràng tầng Security / Presentation (`AuthPrincipal`) khỏi Domain Entity (`UserEntity`), chấm dứt việc gán logic giả mạo vào thực thể nghiệp vụ.
- [x] **II. Dependency Injection with Dishka (MUST)**: Đạt. Tiếp tục sử dụng DI qua FastAPI dependencies và Dishka không bị xáo trộn.
- [x] **V. API Backward Compatibility & Non-Null Contract DTOs (MUST)**: Đạt. Hợp đồng API giữ nguyên cấu trúc phản hồi `ApiResponse[T]`, không phá vỡ bất kỳ endpoint nào của frontend/Zalo Mini App.
- [x] **VII. Single-Responsibility Use Cases (MUST)**: Đạt. Các use case không bị gộp chung, giữ nguyên tính đơn nhiệm.
- [x] **Security & RBAC Standards**: Đạt. Loại bỏ triệt để lỗi logic bảo mật `user_id = 0`, phân quyền RBAC được thực thi chặt chẽ, an toàn hơn.

## Project Structure

### Documentation (this feature)

```text
specs/010-auth-principal-refactor/
├── spec.md              # Đặc tả tính năng
├── checklists/
│   └── requirements.md  # Checklist chất lượng đặc tả
├── plan.md              # Kế hoạch triển khai (tài liệu này)
├── research.md          # Kết quả nghiên cứu kỹ thuật & quyết định thiết kế
├── data-model.md        # Mô hình thực thể định danh & bảo mật
├── quickstart.md        # Hướng dẫn kiểm thử và vận hành
└── contracts/
    └── auth-principal.contract.md # Hợp đồng giao tiếp interface & dependencies
```

### Source Code (repository root)

```text
backend/app/
├── core/
│   ├── principal.py       # [MỚI] Định nghĩa Enum PrincipalType và Model AuthPrincipal
│   ├── context.py         # [CẬP NHẬT] An toàn hóa việc lưu current_user_id (cho phép None khi là API Key)
│   ├── deps.py            # [REFACTOR] get_current_principal, CurrentUser alias, CurrentUserEntity
│   └── permissions.py     # Giữ nguyên các enum quyền hạn
└── homework/
    └── controller.py      # [KIỂM TRA] Bảo đảm controller hoạt động trơn tru với AuthPrincipal
```

## Complexity Tracking

Không có vi phạm Constitution nào cần giải trình. Thiết kế tuân thủ nghiêm ngặt và giúp làm sạch kiến trúc hiện tại.
