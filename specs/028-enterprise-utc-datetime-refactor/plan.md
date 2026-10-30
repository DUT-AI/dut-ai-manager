# Implementation Plan: Chuẩn hóa Kiến trúc Thời gian Toàn diện (Enterprise UTC Datetime)

**Branch**: `028-enterprise-utc-datetime-refactor` | **Date**: 2026-10-30 | **Spec**: [specs/028-enterprise-utc-datetime-refactor/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/028-enterprise-utc-datetime-refactor/spec.md)

**Input**: Feature specification từ `/specs/028-enterprise-utc-datetime-refactor/spec.md`

## Summary

Loại bỏ hoàn toàn anti-pattern `get_current_utc7_time()` trên toàn bộ codebase backend của `dut-ai-manager`. Thiết lập chuẩn kiến trúc thời gian doanh nghiệp:
1. **Lưu trữ chuẩn UTC tuyệt đối**: Toàn bộ cột thời gian trong database chuyển sang `TIMESTAMPTZ` (`DateTime(timezone=True)`).
2. **Cổng DTO tự động thích ứng (Adaptive Ingestion Gate)**: Kiểu dữ liệu `UtcDateTime` tự động phát hiện chuỗi ISO từ Client (hỗ trợ cả chuỗi có offset lẫn chuỗi naive không offset) và chuyển hóa về UTC aware.
3. **Ứng dụng & Domain Layer**: Mọi use case, event handler và scanner sử dụng chuẩn `datetime.now(timezone.utc)`.
4. **Bảo vệ mã nguồn vĩnh viễn**: Bật Linter Ruff rule `DTZ` để tự động chặn các đoạn code sử dụng naive datetime ngay tại IDE và CI/CD.

---

## Technical Context

**Language/Version**: Python 3.12 (uv package manager)  
**Primary Dependencies**: FastAPI, Pydantic V2, SQLAlchemy 2.0, Dishka (DI), Alembic, Dayjs (Frontend)  
**Storage**: PostgreSQL 16+ (chuyển đổi sang `TIMESTAMPTZ`)  
**Testing**: `pytest`, `pytest-asyncio`, `fastapi.testclient`  
**Target Platform**: Linux Server / Docker Container / macOS development  
**Project Type**: Monorepo Web Service (FastAPI Backend + React Frontend + Zalo Mini App)  
**Constraints**: 
- **Zero Downtime / Zero Data Distortion**: Khi chuyển đổi dữ liệu cũ trong PostgreSQL, bắt buộc dùng `AT TIME ZONE 'Asia/Ho_Chi_Minh'` để không bị nhảy sai 7 tiếng.
- **Frontend Backward Compatibility**: Không bắt buộc phải thay đổi đồng loạt toàn bộ màn hình frontend; tầng DTO phải tự động tương thích với format chuỗi hiện tại `YYYY-MM-DDTHH:mm:ss`.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Hiến pháp (Principle) | Trạng thái | Đánh giá & Ràng buộc |
| :--- | :--- | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASS | Type `UtcDateTime` nằm tại Shared Domain/Application. Model mapping độc lập tại Infrastructure. |
| **II. Dependency Injection with Dishka** | ✅ PASS | Giữ nguyên Dishka injection; không can thiệp cơ chế DI. |
| **III. Unified UTC+7 Timezone & DateTime Integrity** | ⚠️ AMENDED | Sửa đổi nguyên tắc III: Chuyển từ "sử dụng hàm `get_current_utc7_time`" sang "Lưu trữ & tính toán nội bộ bằng UTC, quy chiếu biểu diễn theo UTC+7 tại ranh giới". |
| **IV. Event-Driven Decoupling** | ✅ PASS | Các domain event (`MeetingCreated`, `HomeworkCreated`, v.v.) truyền timestamp ISO string UTC chuẩn. |
| **V. API Backward Compatibility** | ✅ PASS | Tầng DTO giữ nguyên schema response `ApiResponse[T]`, tương thích 100% với Frontend và Zalo Mini App. |
| **X. Zero Redundant Backward Compatibility** | ✅ PASS | Xóa bỏ hoàn toàn hàm cũ `get_current_utc7_time()`, refactor trực tiếp toàn bộ call-sites, không để lại alias thừa. |

---

## Project Structure

### Documentation (this feature)

```text
specs/028-enterprise-utc-datetime-refactor/
├── spec.md              # Đặc tả yêu cầu kỹ thuật & kịch bản kiểm thử
├── plan.md              # Kế hoạch thực thi triển khai (File này)
├── research.md          # Kết quả nghiên cứu kỹ thuật & quyết định thiết kế
├── data-model.md        # Thiết kế schema DB, mixin ORM và type DTO
└── quickstart.md        # Hướng dẫn lập trình viên sử dụng chuẩn thời gian mới
```

### Source Code Impact Map

```text
backend/
├── app/
│   ├── shared/
│   │   ├── domain/
│   │   │   └── datetime_types.py          # [NEW] UtcDateTime, IsoDateTime
│   │   ├── infrastructure/
│   │   │   └── base_model.py              # [MODIFY] SQLAlchemyTimestampMixin sang DateTime(timezone=True)
│   ├── utils/
│   │   └── datetime.py                    # [DELETE/REFACTOR] Loại bỏ get_current_utc7_time
│   ├── meeting/                           # [MODIFY] Model, DTOs, Use Cases sang UTC
│   ├── homework/                          # [MODIFY] Model, DTOs, Use Cases sang UTC
│   ├── reminder/                          # [MODIFY] Model, Scanner Use Cases sang UTC
│   ├── bonus_point/                       # [MODIFY] Model, Use Cases sang UTC
│   ├── duty/                              # [MODIFY] Model, Use Cases sang UTC
│   ├── violation/                         # [MODIFY] Model, Event Handlers sang UTC
│   └── rbac/, billing/, user/, expense/   # [MODIFY] Cập nhật created_at/updated_at models
├── alembic/
│   └── versions/                          # [NEW] Migration script ALTER columns to TIMESTAMPTZ
└── pyproject.toml                         # [MODIFY] Bật Ruff rule DTZ
```

---

## Phases of Execution

### Phase 0: Baseline & Infrastructure Preparation
- Tạo module `app.shared.domain.datetime_types` với custom type `UtcDateTime`.
- Viết unit test độc lập cho `UtcDateTime` bao phủ mọi kịch bản input:
  - Chuỗi ISO kèm `Z`
  - Chuỗi ISO kèm offset `+07:00`
  - Chuỗi naive không múi giờ (như `YYYY-MM-DDTHH:mm:ss`) -> Phải tự động đổi về UTC tương ứng với giờ Việt Nam.

### Phase 1: Database Schema & Base Mixin Refactor
- Cập nhật `SQLAlchemyTimestampMixin` trong `base_model.py`:
  - `created_at` và `updated_at` sử dụng `DateTime(timezone=True)`.
  - Default gán `lambda: datetime.now(timezone.utc)`.
- Tạo migration script Alembic:
  - Chuyển đổi các cột `TIMESTAMP WITHOUT TIME ZONE` của các bảng cốt lõi sang `TIMESTAMPTZ` sử dụng mệnh đề `USING column_name AT TIME ZONE 'Asia/Ho_Chi_Minh'`.

### Phase 2: Domain by Domain Migration (Refactor Call-Sites)
Thực hiện lần lượt qua từng domain theo thứ tự ưu tiên:
1. **Core Utilities & Base**: `app/utils/datetime.py` (loại bỏ `get_current_utc7_time`).
2. **Reminder & Tasks**: `app/reminder/` (quét deadline và giờ họp theo UTC).
3. **Meeting**: `app/meeting/` (start_time, end_time, check-in, check-out).
4. **Homework**: `app/homework/` (deadline, submitted_at).
5. **Bonus Point & Violation**: `app/bonus_point/`, `app/violation/`.
6. **Duty & Billing**: `app/duty/`, `app/billing/`, `app/expense/`.

### Phase 3: Linter Enforcement & Verification
- Thêm rule `"DTZ"` vào `[tool.ruff.lint.select]` trong `backend/pyproject.toml`.
- Chạy `ruff check .` để quét sạch toàn bộ các vị trí còn sót lại dùng naive datetime.
- Chạy toàn bộ test suite `pytest` kiểm tra 100% regression.
- Cập nhật Constitution Principle III lên version 1.6.0.
