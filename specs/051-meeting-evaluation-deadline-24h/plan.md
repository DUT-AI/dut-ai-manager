# Implementation Plan: Điều Chỉnh Thời Hạn Đánh Giá Cuộc Họp Từ 72 Giờ Về 24 Giờ (Meeting Evaluation Deadline 24 Hours)

**Branch**: `051-meeting-evaluation-deadline-24h` | **Date**: 2026-11-05 | **Spec**: [specs/051-meeting-evaluation-deadline-24h/spec.md](file:///Users/nguyenhuynh/Documents/dut-ai-manager/specs/051-meeting-evaluation-deadline-24h/spec.md)

**Input**: Feature specification from `specs/051-meeting-evaluation-deadline-24h/spec.md`

---

## Summary

Cập nhật thời hạn bắt buộc hoàn thành đánh giá cuộc họp từ **72 giờ (3 ngày) về lại 24 giờ (1 ngày)** tính từ thời điểm cuộc họp kết thúc (`meeting.end_time`). Tác vụ nền định kỳ sẽ quét và tự động tạo vi phạm kèm cảnh cáo/phạt đối với người tham gia hoặc người phụ trách chưa hoàn thành đánh giá sau 24 giờ, đồng thời cập nhật toàn bộ nội dung thông báo vi phạm và tên job định kỳ hiển thị chuẩn xác mốc "24h".

---

## Technical Context

**Language/Version**: Python 3.12  
**Primary Dependencies**:
- `fastapi>=0.128.0`
- `apscheduler>=3.11.2`
- `sqlalchemy>=2.0`
- `dishka>=1.9.1`  
**Storage**: PostgreSQL 16 (Bảng `meetings`, `meeting_evaluations`, `violations`)  
**Testing**: `pytest>=8.0.0`, `pytest-asyncio`  
**Target Platform**: Linux Container / macOS dev  
**Project Type**: Web Service (Domain Constants & Scheduled Use Case)  
**Performance Goals**: Quét kiểm tra vi phạm hoàn tất trong <200ms cho mỗi lượt quét hàng giờ  
**Constraints**:
- Không làm gián đoạn hoặc thay đổi dữ liệu các bản ghi vi phạm cũ trong quá khứ.
- Không yêu cầu thay đổi cấu trúc bảng cơ sở dữ liệu (Zero Alembic Migration required).
- Đảm bảo tính toán múi giờ UTC tuyệt đối theo Principle III.  
**Scale/Scope**: Áp dụng cho toàn bộ các cuộc họp có bật đánh giá trong hệ thống.

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Nguyên Tắc Hiến Pháp | Đánh Giá Tính Tuân Thủ | Trạng Thái |
| :--- | :--- | :--- |
| **I. Clean Architecture & DDD Boundaries** | Hằng số nghiệp vụ đặt tại tầng Domain (`app.meeting.domain.constants`), logic kiểm tra nằm trong Application Use Case. | **PASS** |
| **III. Enterprise UTC Storage** | Ngưỡng thời gian `now` và `end_bound` sử dụng `datetime.now(timezone.utc)` chuẩn mực. | **PASS** |
| **IV. Event-Driven Decoupling** | Bản ghi vi phạm sau khi tạo tiếp tục kích hoạt thông báo bất đồng bộ qua `EventBus`. | **PASS** |
| **X. Single Source of Truth** | Hằng số `MEETING_EVALUATION_DEADLINE_HOURS = 24` là nguồn chân lý duy nhất cho toàn bộ hệ thống. | **PASS** |
| **XI. Plain Text Notifications** | Thông báo vi phạm sử dụng định dạng plain text sạch sẽ, không chứa raw markdown lộn xộn. | **PASS** |

**Kết luận Gate**: Toàn bộ các tiêu chí đánh giá đều **PASS**.

---

## Project Structure

### Documentation (this feature)

```text
specs/051-meeting-evaluation-deadline-24h/
├── spec.md              # Đặc tả yêu cầu người dùng và tiêu chí thành công
├── plan.md              # Kế hoạch triển khai (File hiện tại)
├── research.md          # Nghiên cứu kỹ thuật, phân tích tác động và quyết định
├── data-model.md        # Mô hình dữ liệu thực thể, hằng số và luồng ra quyết định
├── quickstart.md        # Hướng dẫn kiểm thử và xác minh tính năng
├── contracts/           # Hợp đồng giao thức
│   └── meeting-evaluation-deadline-contract.md  # Ngưỡng thời gian và mẫu văn bản vi phạm
└── checklists/
    └── requirements.md  # Đánh giá độ phủ yêu cầu (16/16 Pass)
```

### Source Code Impact Layout (backend)

```text
backend/
├── app/
│   ├── meeting/
│   │   ├── domain/
│   │   │   ├── constants.py                     # Cập nhật MEETING_EVALUATION_DEADLINE_HOURS = 24
│   │   │   └── __init__.py                      # Re-export hằng số
│   │   └── application/
│   │       └── check_evaluation_deadline_job_use_case.py  # Cập nhật lý do vi phạm "trong vòng 24h"
│   ├── jobs/
│   │   └── meeting_evaluation_checker_job.py    # Cập nhật docstring & log 72h -> 24h
│   └── core/
│       └── scheduler.py                         # Cập nhật job name "Check 24h meeting evaluations deadline"
└── tests/
    └── unit/
        └── test_meeting_evaluation.py           # Cập nhật assertions lý do vi phạm và 24h bounds test
```

---

## Complexity Tracking

> Không có vi phạm kiến trúc nào cần biện minh (Zero violations detected).
