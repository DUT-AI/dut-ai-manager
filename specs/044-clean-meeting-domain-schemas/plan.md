# Implementation Plan: Loại Bỏ `Any` & `getattr`, Chuẩn Hóa Type Safety cho Meeting Domain & Schemas

**Branch**: `044-clean-meeting-domain-schemas` | **Date**: 2026-11-01 | **Spec**: [specs/044-clean-meeting-domain-schemas/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/044-clean-meeting-domain-schemas/spec.md)

**Input**: Làm sạch việc lạm dụng `Any` và `getattr()` trong `meeting_schemas.py`, `participant_schemas.py`, `evaluation_schemas.py`, và `meeting.py`.

---

## Summary

Hiện tại trong các files schemas của Meeting (`meeting_schemas.py`, `participant_schemas.py`, `evaluation_schemas.py`) và entity `meeting.py` xuất hiện dày đặc việc sử dụng `Any` và `getattr()`. 
Nguyên nhân xuất phát từ:
1. Thuộc tính `participants: list[MeetingParticipant]` dạng phẳng ban đầu của Aggregate Root `Meeting` khiến tầng presentation phải bóc tách động.
2. Các phương thức `from_domain` nhận tham số kiểu `Any` thay vì Domain Entity cụ thể.
3. Thói quen phòng thủ quá đà (False Defensive Programming) dẫn đến vi phạm Hiến pháp DUT AI Manager Điều XIV (No Fake Optionals & Fail-Fast Parameter Contracts).

Kế hoạch refactor này thực hiện:
1. Chuẩn hóa Aggregate Root `Meeting` (`backend/app/meeting/domain/meeting.py`):
   - Sử dụng `not p.is_deleted` trực tiếp trong properties `trainers` và `trainees`, xóa bỏ `getattr(p, "is_deleted", False)`.
2. Chuẩn hóa `meeting_schemas.py`:
   - Định kiểu rõ ràng tham số `from_domain(cls, m: DomainMeeting)`.
   - Thay thế toàn bộ `getattr(m, ...)` và `getattr(p, ...)` bằng truy cập thuộc tính trực tiếp `m.trainers`, `m.participants`, `p.user.name`, `p.user.avatar_url`.
3. Chuẩn hóa `participant_schemas.py`:
   - Định kiểu `from_domain(cls, p: MeetingParticipant) -> ParticipantResponse`.
   - Xóa bỏ toàn bộ `getattr(p, ...)`, truy cập trực tiếp `p.id`, `p.user_id`, `p.role`, `p.status`, v.v.
   - Thu hẹp `@model_validator` chỉ dùng cho deserialization từ raw dictionary, không can thiệp vào Domain Entity.
4. Chuẩn hóa `evaluation_schemas.py`:
   - Định kiểu `from_domain(cls, e: MeetingOverallEvaluation)` và `from_domain(cls, e: MeetingEvaluation)`.
   - Xóa bỏ toàn bộ `getattr(e, ...)` và `getattr(s, ...)`, truy cập trực tiếp `e.scores`, `s.criteria_code`, `s.score`, `e.trainer`, `e.reviewer`.
5. Kiểm thử toàn diện: Chạy Ruff linter và toàn bộ pytest domain, use cases, API để đảm bảo 100% không xảy ra regression.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend)  
**Primary Dependencies**: Pydantic V2, FastAPI, Dishka DI  
**Testing**: pytest, ruff  
**Constraints**: 
- Không thay đổi database schema hoặc ORM models.
- Giữ nguyên 100% hợp đồng API JSON trả về cho Frontend.
- Tuân thủ nghiêm ngặt Hiến pháp DUT AI Manager v1.9.0 (Điều I, Điều V, Điều XIV).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASSED | Đảm bảo Domain Entity là trung tâm, Schemas phụ thuộc trực tiếp vào Domain Model với Type Contracts rõ ràng. |
| **V. Non-Null Contract DTOs** | ✅ PASSED | Các DTOs trả về cho frontend giữ nguyên cấu trúc non-null contract đã thống nhất. |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | ✅ PASSED | Loại bỏ hoàn toàn `Any` và `getattr()` phòng thủ giả tạo. Mọi tham số và thuộc tính được type hint chặt chẽ. |

---

## Project Structure

### Documentation (this feature)

```text
specs/044-clean-meeting-domain-schemas/
├── spec.md              # Đặc tả yêu cầu
├── plan.md              # Kế hoạch thực thi (tài liệu này)
├── research.md          # Phân tích nguyên nhân & giải pháp
├── data-model.md        # Cấu trúc Entities & DTOs sau refactor
├── quickstart.md        # Hướng dẫn kiểm thử & xác minh
└── contracts/
    └── mapping-contracts.md # Quy chuẩn chữ ký mapper
```

### Source Code Impact

```text
backend/app/meeting/
├── domain/
│   └── meeting.py              # Xóa bỏ getattr trong trainers/trainees properties
└── schemas/
    ├── meeting_schemas.py      # Xóa bỏ getattr, type hint m: DomainMeeting
    ├── participant_schemas.py  # Xóa bỏ getattr, type hint p: MeetingParticipant
    └── evaluation_schemas.py   # Xóa bỏ getattr, type hint e: DomainEvaluation
```

---

## Planned Phases

- **Phase 0: Research & Root Cause Analysis** -> Hoàn thành trong `research.md`.
- **Phase 1: Design & Type Contracts** -> Hoàn thành trong `data-model.md`, `contracts/mapping-contracts.md`, `quickstart.md`.
- **Phase 2: Task Generation & Execution** -> Chạy `/speckit-tasks` hoặc `/speckit-implement` để thực thi thay đổi code và kiểm thử.
