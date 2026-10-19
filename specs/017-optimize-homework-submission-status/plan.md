# Implementation Plan: Tối Ưu Hóa Tốc Độ Tải Danh Sách Bài Nộp Chi Tiết Bài Tập (DB-First Submission Status)

**Branch**: `017-optimize-homework-submission-status` | **Date**: 2026-10-18 | **Spec**: [spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/017-optimize-homework-submission-status/spec.md)

**Input**: Feature specification from `specs/017-optimize-homework-submission-status/spec.md`

## Summary

Loại bỏ hoàn toàn điểm nghẽn độ trễ khi tải trang chi tiết bài tập (`GET /api/v1/homeworks/{id}/submission-status`). Chuyển đổi use case sang chuẩn **DB-First**, thực hiện **1 câu SQL JOIN duy nhất** để lấy danh sách học viên kèm thông tin `(user_id, name, avatar_url)` thay vì quét toàn bộ bảng User lên RAM. Loại bỏ các cuộc gọi mạng Quiz API dư thừa khi bài tập không yêu cầu Game/Coding, đồng thời dùng `asyncio.gather` song song hóa khi đồng bộ. Giảm thời gian phản hồi từ 10-15s xuống < 100ms.

## Technical Context

**Language/Version**: Python 3.12, TypeScript / React 18  
**Primary Dependencies**: FastAPI, Dishka (IoC/DI), SQLAlchemy 2.0, HTTPX, Ant Design, TanStack Query  
**Storage**: PostgreSQL (`homeworks`, `homework_assignees`, `homework_submissions`, `users`, `permission_requests`)  
**Testing**: pytest  
**Target Platform**: Linux Server / Web (Chrome, Safari, Firefox)  
**Project Type**: Monorepo Web Application (FastAPI backend + Vite React frontend)  
**Performance Goals**: Endpoint `GET /api/v1/homeworks/{id}/submission-status` phản hồi < 100ms  
**Constraints**: Bảo toàn 100% hợp đồng dữ liệu DTO `HomeworkSubmissionStatusResponse`, tuân thủ chuẩn giờ UTC+7 naive datetime.

## Constitution Check

- [x] **Clean Architecture**: Tách biệt rõ ràng tầng Repository (SQL query/join), Application Use Case (tính toán trạng thái nộp bài), Presentation Controller (DTO serialization).
- [x] **Data Integrity**: Dữ liệu đọc từ DB luôn ổn định và nhất quán, không còn hiện tượng chập chờn do mạng ngoài.
- [x] **Regression-Averse**: Giữ nguyên schema DTO, các test case kiểm thử cũ tiếp tục pass 100%.

## Project Structure

### Documentation (this feature)

```text
specs/017-optimize-homework-submission-status/
├── spec.md              # Feature specification
├── plan.md              # Implementation plan (this file)
├── research.md          # Technical research & decisions
├── data-model.md        # Database query & model mapping
├── quickstart.md        # Verification and benchmark guide
├── contracts/           # API contract definitions
│   └── submission-status.json
└── checklists/
    └── requirements.md
```

### Source Code

```text
backend/app/homework/
├── application/
│   ├── get_homework_submission_status_use_case.py   # Refactor to DB-First & use repo join
│   └── sync_homework_use_case.py                    # Ensure parallel sync & type-filter
├── infrastructure/
│   ├── homework_repository.py                       # Add get_assignees_with_user_info(homework_id)
│   └── homework_submission_repository.py            # Existing submission queries
└── tests/
    └── test_homework_api.py                         # Verify unit/integration tests
```

## Implementation Phases

### Phase 0: Research & Benchmarking (research.md)
- Phân tích chi tiết câu lệnh SQL JOIN tối ưu cho `homework_assignees` và `users`.
- Chiến lược trích xuất cấu trúc bài tập con (`ExerciseSummaryDTO`) trực tiếp từ `db_submissions`.
- So sánh thời gian thực thi: Trước (10-15s) vs Sau (< 100ms).

### Phase 1: Design & Contracts (data-model.md, contracts/, quickstart.md)
- Định nghĩa hàm `get_assignees_with_user_info` trong `HomeworkRepository`.
- Chuẩn hóa contract của `HomeworkSubmissionStatusResponse`.
- Soạn thảo `quickstart.md` để kiểm chứng thời gian phản hồi thực tế trên môi trường production/local.
