# Implementation Plan: Tự Động Làm Mới Token Khi Hết Hạn (Auto Refresh Token)

**Branch**: `049-auto-refresh-token` | **Date**: 2026-11-04 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/049-auto-refresh-token/spec.md`

## Summary

Triển khai cơ chế tự động gia hạn phiên đăng nhập ngầm (Silent Token Refresh) cho hệ thống web `dut-ai-manager`. Khắc phục triệt để lỗi tự động đăng xuất khi người dùng thao tác hoặc truy cập trang chủ `/` lúc `access_token` hết hạn. 

Giải pháp bao gồm:
1. **Frontend**: Tái cấu trúc Axios Response Interceptor trong `axiosInstance.ts` với cờ đồng bộ `isRefreshing`, hàng đợi Promise `failedQueue` để xử lý các request đồng thời, loại bỏ điều kiện chặn refresh sai lầm tại route gốc `'/'`, bảo vệ chống vòng lặp vô tận trên các auth endpoints, và cơ chế singleton thông báo khi phiên hết hạn hoàn toàn.
2. **Backend**: Chuẩn hóa phản hồi của endpoint `POST /api/v1/auth/refresh` ném lỗi HTTP `401 Unauthorized` (thông qua `BadRequestException`) khi thiếu token hoặc token hết hạn thay vì trả về HTTP 200 kèm `is_success: false`, đảm bảo Axios interceptor xử lý dứt khoát.

## Technical Context

**Language/Version**: TypeScript 5.x (Frontend) / Python 3.12+ (Backend)

**Primary Dependencies**: React 19, Axios, Ant Design, FastAPI, Pydantic v2, Dishka, PyJWT

**Storage**: HttpOnly Cookies (`access_token`, `refresh_token`), PostgreSQL

**Testing**: `pytest`, `npm run build`

**Target Platform**: Web Browsers (Chrome, Safari, Firefox, Edge) & Mobile Web

**Project Type**: Full-Stack Web Application (Frontend SPA + Backend REST API)

**Performance Goals**: Quá trình làm mới token ngầm và gửi lại các request trong hàng đợi diễn ra trong dưới 1 giây mà người dùng không nhận thấy độ trễ hay giật lag giao diện.

**Constraints**:
- Bảo toàn tương thích ngược cho endpoint `/auth/refresh` (chấp nhận cả cookie `refresh_token` và payload JSON).
- Không được làm gián đoạn hoặc gửi lặp nhiều request refresh đồng thời (Single-flight refresh lock).
- Tuyệt đối ngăn chặn vòng lặp làm mới vô tận khi máy chủ từ chối refresh token.

**Scale/Scope**: Toàn bộ các API calls trong ứng dụng web (`frontend/src`).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú tuân thủ |
|---|---|---|
| **Principle I: Clean Architecture & Practical DDD** | ✅ PASS | Logic sinh và kiểm tra token nằm trọn vẹn trong domain `app.auth` (`TokenService`, `RefreshTokenUseCase`). Tầng controller chỉ giải mã cookie/request và điều phối. |
| **Principle II: Dependency Injection with Dishka** | ✅ PASS | `RefreshTokenUseCase` được đăng ký và giải quyết qua Dishka Provider (`AuthModuleProvider`). |
| **Principle III: Enterprise UTC & Vietnam Display** | ✅ PASS | Thời hạn token (`exp`) được tính toán chuẩn xác theo Unix timestamp từ thời gian UTC (`datetime.now(UTC)`). |
| **Principle V: API Backward Compatibility & Non-Null Contract** | ✅ PASS | `/auth/refresh` duy trì cấu trúc vỏ bọc `ApiResponse[TokenResponse]`. |
| **Principle VI: Idempotency & Network Resilience** | ✅ PASS | Hàng đợi `failedQueue` gom các request đồng thời và chỉ kích hoạt 1 lượt refresh duy nhất, ngăn xung đột phiên. |
| **Principle VIII: Frontend Component Modularity** | ✅ PASS | Thay đổi tập trung hoàn toàn trong hạ tầng mạng `axiosInstance.ts` và `auth.service.ts`, không can thiệp làm biến dạng các component giao diện. |
| **Principle X: Zero Redundant Backward Compatibility** | ✅ PASS | Loại bỏ hoàn toàn các nhánh kiểm tra điều kiện dư thừa/lỗi thời (`window.location.pathname === '/'`). |
| **Principle XIV: No Fake Optionals & Fail-Fast Contracts** | ✅ PASS | Trả về đúng mã HTTP 401 khi thiếu refresh token thay vì trả về 200 kèm body lỗi giả mạo. |

## Project Structure

### Documentation (this feature)

```text
specs/049-auto-refresh-token/
├── spec.md                     # Feature specification
├── plan.md                     # This implementation plan
├── research.md                 # Architectural & business decisions (Phase 0)
├── data-model.md               # State machine & DTO models (Phase 1)
├── quickstart.md               # Automated testing & manual verification guide (Phase 1)
├── contracts/
│   └── auth-refresh-contract.yaml # OpenAPI specification for refresh endpoint
└── checklists/
    └── requirements.md         # Specification quality checklist
```

### Source Code Impact (repository root)

```text
backend/
├── app/
│   └── auth/
│       ├── controller.py                     # Ném BadRequestException 401 khi thiếu refresh token
│       └── application/
│           └── refresh_token_use_case.py     # Ném BadRequestException 401 khi token không hợp lệ hoặc hết hạn
└── tests/
    └── unit/
        └── test_auth_refresh.py              # Unit tests cho endpoint /auth/refresh

frontend/
├── src/
│   ├── services/
│   │   └── axiosInstance.ts                  # Sửa interceptor: loại bỏ chặn '/', lock isRefreshing, queue retry, loop prevention
│   └── features/
│       └── auth/
│           └── context/
│               └── AuthContext.tsx           # Dọn dẹp session khi phiên hết hạn hoàn toàn
```

**Structure Decision**: Thay đổi tinh gọn và chuẩn hóa tập trung tại tầng giao tiếp mạng `axiosInstance.ts` của frontend và endpoint `controller.py` / `use_case.py` của backend. Không thay đổi cấu trúc thư mục hay thêm thư viện phụ thuộc mới.

## Complexity Tracking

*Không có vi phạm hiến pháp cần giải trình.*
