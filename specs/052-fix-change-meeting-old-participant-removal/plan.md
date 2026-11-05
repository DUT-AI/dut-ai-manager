# Implementation Plan: Tái Cấu Trúc Phân Tách Repository Giữa Meeting Và MeetingParticipant

**Branch**: `052-fix-change-meeting-old-participant-removal` | **Date**: 2026-11-06 | **Spec**: [specs/052-fix-change-meeting-old-participant-removal/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/052-fix-change-meeting-old-participant-removal/spec.md)

**Input**: Feature specification from `specs/052-fix-change-meeting-old-participant-removal/spec.md`

---

## Summary

Tái cấu trúc mã nguồn theo nguyên tắc Single Responsibility Principle (SRP):
- `MeetingRepository`: Chỉ quản lý CRUD bảng `meetings`. Loại bỏ toàn bộ logic diffing, đồng bộ và xóa `meeting_participants` bên trong hàm `save()`.
- `ParticipantRepository`: Toàn quyền quản lý CRUD bảng `meeting_participants`. Bổ sung các phương thức: `remove_participant(meeting_id, user_id)`, `add_participant(domain)`, `bulk_create(meeting_id, participants)`, `sync_meeting_participants(meeting_id, new_trainers, new_trainees)`.
- Cập nhật các use case:
  - `ChangeMeetingStrategy.on_created`: Gọi trực tiếp `participant_repo.remove_participant` và `participant_repo.add_participant`.
  - `CreateMeetingUseCase`: Gọi `meeting_repo.save()` sau đó gọi `participant_repo.bulk_create()`.
  - `UpdateMeetingUseCase`: Gọi `meeting_repo.save()` sau đó gọi `participant_repo.sync_meeting_participants()`.
- Phạm vi không thay đổi: Giữ nguyên logic Auto-Discovery, Backend validation `old_meeting_id`, và Frontend smart selection.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend)  
**Primary Dependencies**: `fastapi>=0.128.0`, `sqlalchemy>=2.0`, `dishka>=1.9.1`, `pydantic>=2.0`  
**Storage**: PostgreSQL 16 (Bảng `meetings`, `meeting_participants`, `permission_requests`)  
**Testing**: `pytest>=8.0.0`, `pytest-asyncio`  
**Target Platform**: Linux Container / macOS dev  
**Project Type**: Backend Web Service / Repository Refactoring  
**Performance Goals**: Rút ngắn thời gian thực thi `on_created` và `save()`, loại bỏ thao tác query thừa 30-50 participants  
**Constraints**:
- Tuân thủ Clean Architecture & Dishka Dependency Injection.
- Không thay đổi schema database (Zero Alembic migrations).
- Giữ nguyên các test suite đang hoạt động ổn định.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên Tắc Hiến Pháp | Đánh Giá Tính Tuân Thủ | Trạng Thái |
| :--- | :--- | :--- |
| **I. Clean Architecture & DDD Boundaries** | Phân định rạch ròi 2 Repository theo SRP. `MeetingRepository` quản lý bảng `meetings`, `ParticipantRepository` quản lý bảng `meeting_participants`. | **PASS** |
| **II. Dependency Injection with Dishka** | Inject `ParticipantRepository` vào `ChangeMeetingStrategy` và các use case qua Dishka Provider (`providers.py`). | **PASS** |
| **III. Enterprise UTC Storage** | Đảm bảo mọi so sánh thời gian sử dụng `datetime.now(timezone.utc)`. | **PASS** |
| **IV. Event-Driven Decoupling** | Tiếp tục phát sự kiện `MeetingParticipantTransferred` và `PermissionRequestCreated` bất đồng bộ qua `EventBus`. | **PASS** |
| **VII. Strict Single-Responsibility Use Cases** | `CreateMeetingUseCase`, `UpdateMeetingUseCase`, `CreatePermissionRequestUseCase` giữ đúng 1 method `execute()` duy nhất. | **PASS** |

**Kết luận Gate**: Toàn bộ các tiêu chí đánh giá đều **PASS**.

---

## Project Structure

### Documentation (this feature)

```text
specs/052-fix-change-meeting-old-participant-removal/
├── spec.md              # Đặc tả yêu cầu người dùng và phạm vi refactoring
├── plan.md              # Kế hoạch triển khai (File hiện tại)
├── research.md          # Quyết định kiến trúc và phạm vi non-goals
├── data-model.md        # Thiết kế phân tách Repository và method signatures
├── quickstart.md        # Hướng dẫn kiểm thử và xác minh tính năng
├── contracts/           # Hợp đồng giao thức
│   └── change-meeting-contract.md  # Chi tiết endpoint và chuyển đổi dữ liệu
└── checklists/
    └── requirements.md  # Đánh giá độ phủ yêu cầu (Pass toàn bộ)
```

### Source Code Impact Layout (Backend Only)

```text
backend/
├── app/
│   ├── meeting/
│   │   ├── application/
│   │   │   ├── create_meeting_use_case.py       # Sử dụng participant_repo.bulk_create
│   │   │   └── update_meeting_use_case.py       # Sử dụng participant_repo.sync_meeting_participants
│   │   └── infrastructure/
│   │       └── repositories/
│   │           ├── meeting_repository.py        # Tinh gọn save() chỉ cập nhật bảng meetings
│   │           └── participant_repository.py    # Bổ sung remove_participant, add_participant, bulk_create, sync_meeting_participants
│   └── permission_request/
│       ├── application/
│       │   └── strategies/
│       │       └── change_meeting_strategy.py   # Rút và thêm participant trực tiếp qua participant_repo
│       └── providers.py                         # Inject participant_repo vào ChangeMeetingStrategy
└── tests/
    ├── unit/
    │   ├── test_change_meeting_permission_request.py  # Cập nhật mock & assert participant_repo
    │   └── test_meeting_use_cases.py                  # Xác minh Create/Update meeting use cases
    └── api/
        └── test_change_meeting_api.py                 # E2E integration test chuyển ca
```

---

## Complexity Tracking

> Quyết định thiết kế phân tách Repository làm giảm độ phức tạp của `MeetingRepository.save()` từ O(N) diffing xuống O(1) chỉ lưu entity `Meeting`, tăng tính module hóa và không gây ảnh hưởng đến các thành phần khác.
