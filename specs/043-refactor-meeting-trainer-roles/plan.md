# Implementation Plan: Tách Biệt Vai Trò Trainer & Trainee Trong Quản Lý Buổi Học

**Branch**: `043-refactor-meeting-trainer-roles` | **Date**: 2026-11-01 | **Spec**: [specs/043-refactor-meeting-trainer-roles/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/043-refactor-meeting-trainer-roles/spec.md)

**Input**: Yêu cầu refactor: Phân loại participant thành Trainer hoặc Trainee, form có 2 nơi nhập, bảng `meeting_participants` có thêm trường `role`, `created_by` chỉ mang ý nghĩa audit người tạo, Trainer là người phụ trách và có toàn quyền trong meeting.

---

## Summary

Hiện tại hệ thống đồng nhất Trainer với `meeting.created_by` (người bấm nút tạo meeting), trong khi bảng `meeting_participants` không có trường phân biệt vai trò. Điều này khiến các cuộc họp do Admin/Leader tạo hộ không trao quyền điều hành cho Trainer thực tế, đồng thời làm sai lệch luồng đánh giá và nhắc việc.

Kế hoạch refactor này thực hiện:
1. Thêm cột `role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE'` vào bảng `meeting_participants` qua Alembic migration, có data backfill an toàn.
2. Bổ sung `ParticipantRole` enum (`TRAINER`, `TRAINEE`) vào Domain Model và ánh xạ qua Entity `MeetingParticipant`.
3. Bổ sung các helper methods trong `Meeting` entity (`trainers`, `trainees`, `is_trainer`, `is_trainee`) hỗ trợ nhiều Trainer bình đẳng (không cần Trainer đại diện chính).
4. Cập nhật DTO `MeetingCreate`, `MeetingUpdate`, `ParticipantResponse`, `MeetingResponse` hỗ trợ `trainer_ids` và `trainee_ids` (hỗ trợ nhiều Trainer).
5. Nâng cấp phân quyền trong `dependencies.py` cấp toàn quyền điều hành, điểm danh và đánh giá buổi học cho tất cả các Trainer của meeting.
6. Cập nhật giao diện `MeetingModal.tsx` gồm 2 khu vực nhập: Chọn Trainer(s) phụ trách và Chọn Trainee(s) tham gia (kèm chọn nhanh theo Team).
7. Tách giao diện người tham gia thành **2 bảng riêng biệt**: `TrainerListTable` (Bảng Trainer) và `TraineeListTable` (Bảng Trainee) trong cả `MeetingParticipantsTab.tsx` và `ParticipantListModal.tsx`.
8. Hỗ trợ chọn Trainer trong `TraineeEvaluationModal.tsx` khi buổi học có nhiều Trainer phụ trách.
9. Đồng bộ luồng đánh giá và thông báo nhắc nhở (`MeetingEvaluationTaskScanner`) quét toàn bộ danh sách `meeting.trainers`.

---

## Technical Context

**Language/Version**: Python 3.12 (Backend) / TypeScript React (Frontend)  
**Primary Dependencies**: FastAPI, Dishka DI, SQLAlchemy 2.0, Alembic, Ant Design, TanStack React Query  
**Storage**: PostgreSQL (`meetings`, `meeting_participants`), SQLite in-memory cho Unit Testing  
**Testing**: pytest, pytest-asyncio, vitest / npm build  
**Constraints**: 
- Zero-Downtime Migration: Không làm mất hoặc hỏng dữ liệu các buổi họp cũ.
- Strict Single-Responsibility & Type Safety theo Hiến pháp DUT AI Manager v1.9.0.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASSED | `MeetingParticipant` là entity con thuộc Aggregate Root `Meeting`. Mọi ràng buộc vai trò được gói gọn trong domain logic. |
| **II. Dependency Injection with Dishka** | ✅ PASSED | Các repository và use case được resolve qua Dishka. |
| **III. Enterprise UTC Storage** | ✅ PASSED | Mọi timestamp điểm danh giữ nguyên chuẩn UTC ISO 8601. |
| **VII. Strict Single-Responsibility Use Case** | ✅ PASSED | Use case `CreateMeetingUseCase` và `UpdateMeetingUseCase` chịu trách nhiệm lưu participants với role tương ứng. |
| **X. Zero Redundant Backward Compatibility** | ✅ PASSED | Tuyệt đối KHÔNG fallback qua `user_ids` hay `created_by`. Script migration chuẩn hóa 100% dữ liệu lịch sử bằng cách cập nhật hoặc chèn thêm 1 dòng Trainer là `created_by`. |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | ✅ PASSED | `trainer_ids` và `trainee_ids` được định kiểu danh sách rõ ràng (`list[int] = Field(default_factory=list)`), cho phép buổi tự học nhóm không có Trainer (`trainer_ids=[]`), tuân thủ strict contract. |

---

## Project Structure

### Documentation (this feature)

```text
specs/043-refactor-meeting-trainer-roles/
├── spec.md              # Đặc tả yêu cầu nghiệp vụ
├── plan.md              # Kế hoạch thực thi (tài liệu này)
├── research.md          # Phân tích kỹ thuật & chiến lược migration
├── data-model.md        # Mô hình dữ liệu & cấu trúc DTO
├── quickstart.md        # Kịch bản kiểm thử độc lập
└── contracts/
    └── meeting-api.md   # Hợp đồng API chi tiết
```

### Source Code Impact

```text
backend/
├── alembic/versions/
│   └── 040_add_role_to_meeting_participants.py # Migration thêm cột role & backfill
├── app/
│   ├── meeting/
│   │   ├── domain/
│   │   │   ├── value_objects.py # Thêm ParticipantRole enum
│   │   │   ├── participant.py   # Thêm trường role vào entity
│   │   │   └── meeting.py       # Helper methods: trainers, trainees, is_trainer
│   │   ├── infrastructure/
│   │   │   └── model.py         # ORM model meeting_participants thêm cột role
│   │   ├── schemas/
│   │   │   ├── meeting_schemas.py     # Thêm trainer_ids, trainee_ids, trainers list
│   │   │   └── participant_schemas.py # Thêm role vào response
│   │   ├── application/
│   │   │   ├── create_meeting_use_case.py
│   │   │   └── update_meeting_use_case.py
│   │   └── controllers/
│   │       └── dependencies.py  # Cấp quyền meeting cho is_trainer
│   └── reminder/
│       └── application/
│           └── scanners/
│               └── meeting_evaluation_scanner.py # Quét meeting.trainers
└── tests/
    ├── api/test_meeting_api.py
    └── unit/test_meeting_use_cases.py

frontend/
└── src/
    └── features/
        └── meeting/
            ├── types/meeting.types.ts
            ├── components/
            │   ├── MeetingModal.tsx              # Tách 2 ô chọn Trainer và Trainee
            │   ├── MeetingParticipantsTab.tsx    # Chứa 2 Section riêng biệt cho Trainer & Trainee
            │   ├── ParticipantListModal.tsx      # Tách 2 Bảng: Trainer & Trainee
            │   ├── TraineeEvaluationModal.tsx    # Chọn Trainer khi meeting có nhiều Trainer
            │   └── participants/
            │       ├── TrainerListTable.tsx      # Bảng danh sách Trainer phụ trách
            │       ├── TraineeListTable.tsx      # Bảng danh sách Trainee tham gia
            │       └── ParticipantMobileList.tsx # Chia 2 nhóm Trainer & Trainee
            └── hooks/useMeetings.ts
```

---

## Planned Phases

- **Phase 0: Research & Migration Strategy** -> Đã hoàn thành trong `research.md`.
- **Phase 1: Design & Contracts** -> Đã hoàn thành trong `data-model.md`, `contracts/meeting-api.md`, `quickstart.md`.
- **Phase 2: Task Breakdown** -> Chạy `/speckit-tasks` để sinh checklist các công việc cụ thể.
