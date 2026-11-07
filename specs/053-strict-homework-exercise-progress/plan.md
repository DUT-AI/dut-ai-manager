# Implementation Plan: Chuẩn hóa nghiêm ngặt tiến độ bài tập con và tách biệt Game Quiz

**Branch**: `053-strict-homework-exercise-progress` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/053-strict-homework-exercise-progress/spec.md`

## Summary

Loại bỏ toàn bộ cơ chế suy diễn mập mờ (fallbacks) và tách biệt dứt khoát giữa bài tập Coding con và Game Quiz. Cung cấp danh mục bài tập con chính thức (`coding_exercises`) trực tiếp từ API chi tiết bài tập (`GET /homeworks/{id}`), đảm bảo học viên luôn thấy đủ các bài con (kể cả bài chưa làm). Đồng thời, chuẩn hóa modal Admin (không gom Game vào bài con tạo thành bài ảo "Bài tập chung") và sửa lỗi hiển thị điểm/tỷ lệ đúng của Game Quiz.

## Technical Context

**Language/Version**: Python 3.12 (FastAPI), TypeScript 5.6 (React 18 + Vite)  
**Primary Dependencies**: FastAPI, Pydantic V2, Dishka, SQLAlchemy 2.0, Ant Design 5, TanStack Query V5, Dayjs  
**Storage**: PostgreSQL 16 (Bảng `homeworks`, `homework_submissions`, `homework_assignees`)  
**Testing**: pytest (Backend), npm build / type-check (Frontend)  
**Target Platform**: Web application (Desktop & Mobile)  
**Project Type**: Full-stack web application (FastAPI backend + React frontend)  
**Performance Goals**: API response time < 100ms cho việc lấy chi tiết bài tập kèm danh mục bài con  
**Constraints**: Tuân thủ Clean Architecture, Non-Null Contract DTOs (Principle V), Không phá vỡ tương thích ngược API  
**Scale/Scope**: Tác động trực tiếp vào module Homework (Backend `app/homework` và Frontend `features/homework`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Principle I: Clean Architecture & Practical DDD Boundaries**: DTO mở rộng ở tầng Application, Logic tách nhóm ở Frontend Utils, không nhúng logic database vào Controller.
- [x] **Principle II: Dependency Injection with Dishka**: Sử dụng provider Dishka hiện có để inject `QuizApiClient` và Repository vào `GetHomeworkDetailUseCase`.
- [x] **Principle III: Enterprise UTC Storage**: Giữ nguyên thời gian nộp bài UTC ISO string.
- [x] **Principle V: API Backward Compatibility & Non-Null Contract DTOs**: Thêm trường `coding_exercises` vào `HomeworkResponseDetail` với giá trị mặc định là empty list, không làm thay đổi các trường hiện có.
- [x] **Principle VII: Strict Single-Responsibility Use Cases**: `GetHomeworkDetailUseCase` giữ nguyên trách nhiệm duy nhất là lấy chi tiết bài tập theo ID.

## Project Structure

### Documentation (this feature)

```text
specs/053-strict-homework-exercise-progress/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── homework_detail_contract.md
│   └── group_submissions_contract.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit-tasks command)
```

### Source Code

```text
backend/app/homework/
├── application/
│   ├── dtos.py                                       # Thêm coding_exercises vào HomeworkResponseDetail
│   └── get_homework_detail_use_case.py                # Lấy danh mục coding_exercises gắn vào DTO
├── controller.py                                     # Route GET /{homework_id} giữ nguyên signature
└── providers.py                                      # Dishka provider đăng ký phụ thuộc cho UseCase

frontend/src/features/homework/
├── types/homework.types.ts                           # Thêm coding_exercises vào homeworkSchema
├── utils/submissionUtils.ts                          # Strict grouping: chỉ nhận CODING, cấm tạo "Bài tập chung"
├── components/
│   ├── SubmissionHistoryModal.tsx                    # Tách Tab Coding & Game cho Admin Modal
│   ├── SubmissionItemCard.tsx                        # Sửa hiển thị điểm & tỷ lệ đúng động của Game
│   └── UnifiedSubmissionTimeline.tsx                 # Bỏ text hardcode (100%)
└── pages/
    └── MyHomeworkDetailPage.tsx                      # Truyền allExercises từ homework.coding_exercises
```

**Structure Decision**: Cấu trúc Web application 2 tầng (FastAPI Backend + React Frontend Monorepo).

## Complexity Tracking

*Không có vi phạm Constitution nào cần giải trình.*
