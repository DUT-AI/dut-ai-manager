# Implementation Plan: Đơn Xin Đổi Buổi Sinh Hoạt / Meeting (`CHANGE_MEETING`)

**Branch**: `007-change-meeting-permission-request` | **Date**: 2026-10-07 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from [specs/007-change-meeting-permission-request/spec.md](spec.md)

## Summary

Bổ sung loại danh mục yêu cầu mới `CHANGE_MEETING` vào hệ thống đơn từ (`PermissionRequest`), cho phép thành viên chuyển đổi linh hoạt từ Meeting A sang Meeting B (hoặc đăng ký mới vào Meeting B nếu chưa có ca). Hệ thống tự động tính toán số ghế khả dụng theo công thức $\text{MAX\_SEATS} - (\text{Participant active} - \text{Đơn ABSENCE})$, thực hiện khóa giao dịch nguyên tử (Pessimistic Lock) để chống race condition, tự động duyệt ngay (Auto-Approve), điều phối participant giữa 2 meeting, dọn dẹp đơn xin vắng/trễ cũ tại ca cũ, và phát sự kiện `MeetingParticipantTransferred` để gửi thông báo đa kênh (Telegram/Zalo/Discord).

---

## Technical Context

**Language/Version**: Python 3.11+ (Backend) | TypeScript 5.x (Frontend & Zalo Mini App)

**Primary Dependencies**: 
- Backend: FastAPI, SQLAlchemy 2.0, Dishka IoC, Pydantic v2, Loguru.
- Frontend & Mini App: React 18+, Vite, Ant Design, Tailwind CSS, Zalo Mini App SDK.

**Storage**: PostgreSQL 16 (Alembic for schema migrations).

**Testing**: `pytest`, `pytest-asyncio` for unit/integration tests.

**Target Platform**: Docker container / Linux server / Web browsers & Zalo App.

**Project Type**: Multi-tier Web Application (FastAPI REST API + Web Dashboard + Zalo Mini App).

**Performance Goals**: API response time $< 100\text{ms}$ cho việc nộp và xử lý đổi ca.

**Constraints**:
- Single transaction atomicity cho việc rút/thêm participant và vô hiệu hóa đơn vắng cũ.
- Chuẩn hóa thời gian Naive UTC+7 (`app.utils.datetime.get_current_utc7_time()`).
- Tách use case theo nguyên tắc đơn nhiệm (Single-Responsibility Use Case).

**Scale/Scope**: Hỗ trợ đồng thời 100+ học viên, phòng học tối đa 35 chỗ/buổi.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Constitution | Trạng thái | Đánh giá sự tuân thủ |
|---|---|---|
| **I. Clean Architecture & Practical DDD** | **PASS** | Tách bạch 4 tầng: Domain (`entity.py`, `value_objects.py`, `events.py`), Application (`create_change_meeting_request_use_case.py`), Infrastructure (`model.py`, `repository.py`), Presentation (`controller.py`, `schemas.py`). |
| **II. Dependency Injection with Dishka** | **PASS** | Mọi repository và use case mới đều được khai báo trong `providers.py` và inject bằng `FromDishka[...]`. |
| **III. Unified UTC+7 Timezone** | **PASS** | Tất cả logic so sánh thời gian (`now < meeting.start_time`) sử dụng `get_current_utc7_time()`. |
| **IV. Event-Driven Decoupling** | **PASS** | Tác vụ gửi thông báo (Zalo/Discord) tách biệt qua `EventBus` và `EventHandler`, không làm nghẽn HTTP response. |
| **V. API Backward Compatibility & Non-Null Contracts** | **PASS** | Sử dụng chuẩn phong bì `ApiResponse[T]` và DTO trả về đầy đủ các trường quan hệ (`meeting`, `old_meeting`). |
| **VI. Idempotency & Network Resilience** | **PASS** | Giao dịch điều phối participant bảo vệ bằng Pessimistic Lock trên bản ghi meeting đích. |
| **VII. Single-Responsibility Use Cases** | **PASS** | Tạo use case riêng biệt trong file chuyên dụng `app/permission_request/application/create_change_meeting_request_use_case.py`. |
| **VIII. Frontend Component Modularity** | **PASS** | Tách form chọn đổi buổi học thành component riêng biệt trong `components/` của Zalo Mini App và Web Frontend. |

---

## Project Structure

### Documentation (this feature)

```text
specs/007-change-meeting-permission-request/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan
├── research.md          # Technical research & architectural decisions (Phase 0)
├── data-model.md        # Data model & state lifecycle diagram (Phase 1)
├── contracts/           # API contract OpenAPI 3.1 (Phase 1)
│   └── permission-request-api.yaml
├── quickstart.md        # Verification & test guide (Phase 1)
└── checklists/          # Quality verification checklist
    └── requirements.md
```

### Source Code Layout

```text
backend/
├── alembic/versions/
│   └── xxxx_add_change_meeting_and_old_meeting_id.py  # Migration mới
├── app/
│   ├── permission_request/
│   │   ├── domain/
│   │   │   ├── value_objects.py  # Thêm CHANGE_MEETING vào RequestCategory
│   │   │   ├── entity.py         # Thêm old_meeting_id và old_meeting
│   │   │   └── events.py         # Thêm MeetingParticipantTransferred (hoặc dùng PermissionRequestCreated)
│   │   ├── application/
│   │   │   ├── create_change_meeting_request_use_case.py # Use case chuyên biệt
│   │   │   ├── event_handlers.py # Handler gửi thông báo Zalo/Discord
│   │   │   └── __init__.py
│   │   ├── infrastructure/
│   │   │   ├── model.py          # Thêm column old_meeting_id và relationship old_meeting
│   │   │   └── repository.py     # Thêm query hủy đơn vắng cũ và lock meeting
│   │   ├── presentation/
│   │   │   ├── controller.py     # Endpoint nộp đơn
│   │   │   └── schemas.py        # Thêm old_meeting_id vào request/response schemas
│   │   └── providers.py          # Đăng ký use case mới vào Dishka
│   └── meeting/
│       ├── domain/
│       │   └── entity.py         # Bổ sung calculate_available_seats
│       ├── application/
│       │   └── get_upcoming_meetings_with_seats_use_case.py # Use case lấy danh sách ca kèm số ghế
│       ├── presentation/
│       │   ├── controller.py     # Endpoint /api/v1/meetings/available-seats
│       │   └── schemas.py
│       └── providers.py
└── tests/
    └── test_change_meeting_permission_request.py # Test suite tự động

zalo-mini-app/dut-manager/
├── src/
│   ├── types/
│   │   └── permission.types.ts   # Thêm CHANGE_MEETING enum & schema
│   ├── features/
│   │   └── permission_request/
│   │       ├── PermissionFormModal.tsx    # Bổ sung UI chọn ca cũ & ca mới kèm badge số ghế
│   │       ├── PermissionDetailModal.tsx  # Hiển thị thông tin ca chuyển từ đâu sang đâu
│   │       ├── PermissionList.tsx         # Tag badge cho CHANGE_MEETING
│   │       └── usePermissionManagement.ts # Logic submit và fetch meetings
```

---

## Complexity Tracking

> Không có vi phạm Constitution cần giải trình. Thiết kế bám sát kiến trúc hiện tại của dự án.
