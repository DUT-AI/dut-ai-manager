# Implementation Plan: Nhắc Nhở Mentor/Trainer Hoàn Tất Đánh Giá Buổi Học

**Branch**: `042-mentor-meeting-eval-reminder` | **Date**: 2026-11-01 | **Spec**: [specs/042-mentor-meeting-eval-reminder/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/042-mentor-meeting-eval-reminder/spec.md)

**Input**: Phản ánh từ người dùng "Hiện tại tôi thấy hệ thống thông báo nhắc nhở mentor đánh giá meeting chưa hoạt động, tôi thấy nó không thông báo cho tôi".

---

## Summary

Hiện tại, `MeetingEvaluationTaskScanner` chỉ duyệt mảng `valid_participants` (học viên/Trainee) và bỏ quên hoàn toàn Mentor/Trainer (`meeting.created_by`). Hơn nữa, thuộc tính `meeting.evaluation_deadline` trong entity `Meeting` đang hardcode `hours=24` (thay vì 72h theo hằng số hệ thống `MEETING_EVALUATION_DEADLINE_HOURS = 72`), khiến Scanner dừng nhắc nhở quá sớm sau 24h và đường dẫn `action_url` bị sai route 404.

Kế hoạch này nâng cấp:
1. Đồng bộ `meeting.evaluation_deadline` thành 72h chuẩn xác (`MEETING_EVALUATION_DEADLINE_HOURS`).
2. Inject `MeetingOverallEvaluationRepository` vào `MeetingEvaluationTaskScanner` và cấu hình Dishka provider.
3. Bổ sung luồng quét Mentor (`meeting.created_by`):
   - Nhắc Mentor nộp Đánh giá tổng thể buổi học nếu chưa có `MeetingOverallEvaluation`.
   - Nhắc Mentor hoàn tất đánh giá các học viên tham gia nếu còn bạn chưa được chấm điểm.
4. Sửa `action_url` chuẩn thành `/dashboard/meetings/{meeting.id}` và mở rộng cửa sổ quét buổi họp lên 5 ngày.
5. Viết unit & integration tests kiểm thử độc lập cho cả 3 kịch bản nhắc việc.

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**: Dishka DI, SQLAlchemy 2.0, Pydantic V2, APScheduler  
**Storage**: PostgreSQL / SQLite in-memory, các bảng `meetings`, `meeting_participants`, `meeting_evaluations`, `meeting_overall_evaluations`, `notifications`  
**Testing**: pytest, pytest-asyncio  
**Constraints**: 
- Bảo toàn cơ chế Deduplication: Không gửi trùng lặp thông báo trong cùng một mốc `ReminderStage`.
- Tuân thủ Hiến pháp DUT AI Manager v1.9.0 (No Fake Optionals, Strict Parameter Contracts, Single-Responsibility).

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên tắc | Đánh giá | Ghi chú |
| :--- | :---: | :--- |
| **I. Clean Architecture & Practical DDD** | ✅ PASSED | `MeetingEvaluationTaskScanner` nằm ở tầng application của Reminder, điều phối repository của Meeting. |
| **II. Dependency Injection with Dishka** | ✅ PASSED | Đăng ký dependency `MeetingOverallEvaluationRepository` qua Dishka provider tại `reminder/providers.py`. |
| **III. Enterprise UTC Storage** | ✅ PASSED | Tất cả so sánh thời gian sử dụng `ensure_utc` và `UTC`. |
| **VII. Strict Single-Responsibility Use Case** | ✅ PASSED | Scanner giữ nguyên interface `scan_pending_tasks(now)`. |
| **X. Zero Redundant Backward Compatibility** | ✅ PASSED | Sửa trực tiếp logic sai lệch, không duy trì cờ giả lập 24h cũ. |
| **XIV. No Fake Optionals & Fail-Fast Parameter Contracts** | ✅ PASSED | Mọi tham số dependency trong constructor scanner đều bắt buộc. |

---

## Project Structure

### Documentation (this feature)

```text
specs/042-mentor-meeting-eval-reminder/
├── spec.md              # Đặc tả yêu cầu nghiệp vụ
├── plan.md              # Kế hoạch thực thi (tài liệu này)
├── research.md          # Phân tích nguyên nhân gốc rễ & quyết định kỹ thuật
├── data-model.md        # Cấu trúc Candidate Task & luồng quét
├── quickstart.md        # Kịch bản kiểm thử độc lập
└── contracts/
    └── notification-contracts.md # Hợp đồng payload thông báo
```

### Source Code Impact

```text
backend/
├── app/
│   ├── meeting/
│   │   └── domain/
│   │       └── meeting.py  # Sửa evaluation_deadline dùng MEETING_EVALUATION_DEADLINE_HOURS = 72
│   └── reminder/
│       ├── providers.py    # Inject MeetingOverallEvaluationRepository vào scanner
│       └── application/
│           └── scanners/
│               └── meeting_evaluation_scanner.py # Bổ sung quét Mentor & sửa action_url
└── tests/
    └── unit/
        └── test_reminder_use_cases.py # Thêm unit tests kiểm thử nhắc nhở Mentor
```

---

## Planned Phases

- **Phase 0: Research & Root Cause Analysis** -> Đã hoàn thành trong `research.md`.
- **Phase 1: Design & Contracts** -> Đã hoàn thành trong `data-model.md`, `contracts/`, `quickstart.md`.
- **Phase 2: Task Breakdown** -> Chạy `/speckit-tasks` để phân rã checklist hành động chi tiết.
