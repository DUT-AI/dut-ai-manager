# Implementation Plan: Cho phép người tạo buổi sinh hoạt không phải Admin thực hiện đánh giá buổi học và học viên

**Branch**: `026-fix-creator-meeting-evaluation` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/026-fix-creator-meeting-evaluation/spec.md`

## Summary

Khắc phục lỗi người tạo buổi sinh hoạt không phải Admin bị mất nút đánh giá trên giao diện người dùng và bị từ chối quyền đánh giá ở tầng Backend:
1. **Backend Data & DTO**: Ghi nhận chính xác `creator_id` của người tạo trong `CreateMeetingUseCase` và lưu vào cột `created_by` của bảng `meetings`; bổ sung trường `created_by: int | None = None` vào `MeetingResponse` và `MeetingDetailResponse` DTO để client nhận diện chủ sở hữu.
2. **Backend RBAC & Ownership**: Thay thế ràng buộc cứng `hasPermission(MeetingPermission.CREATE)` tại 2 endpoint đánh giá tổng thể (`/evaluations/overall`) và đánh giá học viên (`/evaluations/trainer`) bằng cơ chế kiểm tra quyền sở hữu cuộc họp (Resource Ownership: Quản trị viên HOẶC Người tạo cuộc họp HOẶC Trainer được phân công).
3. **Frontend UI Visibility**: Chuẩn hóa điều kiện `isTrainer` trên Web Frontend và Zalo Mini App với ép kiểu an toàn `Number(meeting.created_by) === Number(currentUserId)`, phục hồi đầy đủ nút "Trainer đánh giá buổi học", nút "Đánh giá" từng học viên, và nút "Bật Đánh giá 2 chiều".

## Technical Context

**Language/Version**: Python 3.11+ (Backend), TypeScript 5+ (Web Frontend & Zalo Mini App)  
**Primary Dependencies**: FastAPI, SQLAlchemy 2.0, Dishka DI, Pydantic v2, React 19, Ant Design v5, Tailwind CSS, Zalo Mini App SDK  
**Storage**: PostgreSQL (bảng `meetings`, `meeting_evaluations`, `meeting_overall_evaluations`)  
**Testing**: Pytest (Backend unit & API integration), Vite build check (Frontend & Zalo Mini App)  
**Target Platform**: Linux Server (Backend REST API), Web Desktop/Mobile Browser (Frontend), Zalo Platform (Mini App)  
**Project Type**: Web Service + Single Page Application + Mobile Mini App  
**Performance Goals**: API phản hồi đánh giá < 200ms; hiển thị nút và render trạng thái đánh giá tức thì (< 100ms)  
**Constraints**: Tuân thủ nghiêm ngặt DUT AI Manager Constitution v1.5.0; Zero Secret Leakage; Zero Regression đối với quyền Admin và luồng đánh giá của Trainee  
**Scale/Scope**: Áp dụng cho toàn bộ các buổi sinh hoạt chuyên đề, câu lạc bộ và lớp học trên hệ thống  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc Constitution | Đánh giá tuân thủ | Trạng thái |
| :--- | :--- | :---: |
| **I. Clean Architecture & Practical DDD Boundaries (MUST)** | Thực thể `Meeting` giữ nguyên cấu trúc kế thừa `BaseEntity`. Logic kiểm tra quyền được đặt tại Presentation Layer (FastAPI dependencies), không làm ô nhiễm Domain Layer. | **PASS** |
| **II. Dependency Injection with Dishka (MUST)** | Mọi Use Case và Repository tiếp tục được inject thông qua Dishka Provider (`providers.py`). Không khởi tạo ad-hoc. | **PASS** |
| **III. Unified UTC+7 Timezone Integrity (MUST)** | Mọi mốc thời gian đánh giá và kiểm tra hạn chót 24h sử dụng `get_current_utc7_time()`. | **PASS** |
| **IV. Event-Driven Decoupling (MUST)** | Sự kiện `MeetingCreated` tiếp tục được phát tán qua `EventBus` độc lập với luồng lưu trữ. | **PASS** |
| **V. API Backward Compatibility & Non-Null Contract DTOs (MUST)** | Thêm `created_by: int \| None` vào `MeetingResponse` là additive change, giữ nguyên cấu trúc envelope `ApiResponse[T]`, khớp 100% với schema client đã khai báo. | **PASS** |
| **VII. Strict Single-Responsibility Use Cases (MUST)** | Không tạo Use Case đa năng. `CreateMeetingUseCase` giữ nguyên 1 method `execute(...)` duy nhất. | **PASS** |
| **VIII. Frontend Component Modularity (MUST)** | Không gộp thêm component nguyên khối. Duy trì cấu trúc phân rã `MeetingHeroHeader`, `MeetingParticipantsTab`, và subcomponents. | **PASS** |
| **IX. Pure Composition Over Base Use Cases (MUST)** | Không dùng Base Use Case. | **PASS** |
| **X. Zero Redundant Backward Compatibility (MUST)** | Sửa trực tiếp các call sites và interfaces hiện hữu, không tạo các wrapper compatibility rác. | **PASS** |

## Project Structure

### Documentation (this feature)

```text
specs/026-fix-creator-meeting-evaluation/
├── spec.md              # Feature specification (/speckit-specify output)
├── plan.md              # This implementation plan (/speckit-plan output)
├── research.md          # Phase 0 technical research & decisions
├── data-model.md        # Phase 1 domain entities, ORM, DTO models
├── quickstart.md        # Phase 1 end-to-end validation scenarios
├── contracts/           # Phase 1 API & UI visibility contracts
│   └── meeting-evaluation-contracts.md
└── checklists/
    └── requirements.md  # Specification quality checklist
```

### Source Code (repository root)

```text
backend/
├── app/
│   └── meeting/
│       ├── domain/
│       │   └── entity.py                        # Meeting entity & evaluation checks
│       ├── application/
│       │   └── create_meeting_use_case.py       # Nhận và gán creator_id vào Meeting
│       ├── infrastructure/
│       │   ├── model.py                         # to_entity / from_entity mapping
│       │   └── repository.py                    # save() gán orm.created_by
│       ├── controller.py                        # create_meeting & check_meeting_evaluation_permission
│       └── schemas.py                           # MeetingResponse bổ sung created_by
└── tests/
    ├── unit/
    │   └── test_meeting_evaluation.py           # Unit tests
    └── api/
        └── test_meeting_api.py                  # API permission tests

frontend/
└── src/
    └── features/
        └── meeting/
            ├── components/
            │   ├── MeetingHeroHeader.tsx        # isTrainer check & Overall Eval button
            │   ├── MeetingParticipantsTab.tsx   # isTrainer check & pass prop to list/table
            │   └── ParticipantActionButtons.tsx # Trainee evaluate button
            └── types/
                └── meeting.types.ts             # Meeting schemas

zalo-mini-app/
└── dut-manager/
    └── src/
        └── pages/
            └── MeetingDetailPage.tsx            # isTrainer evaluation button logic
```

**Structure Decision**: Áp dụng mô hình chuẩn của dự án: Clean Architecture phía Backend (`backend/app/meeting`), modular feature architecture phía Frontend (`frontend/src/features/meeting`), và trang chi tiết buổi học tại Zalo Mini App (`zalo-mini-app/.../MeetingDetailPage.tsx`).

## Complexity Tracking

> Không có vi phạm Constitution nào cần miễn trừ. Mọi thay đổi đều tinh gọn, giải quyết chính xác nguyên nhân gốc rễ và tuân thủ tuyệt đối các quy tắc kiến trúc.
