# Research & Technical Decisions: Tối Ưu Và Dọn Dẹp Domain Homework

**Feature**: `003-homework-cleanup` | **Date**: 2026-09-25

---

## 1. Loại bỏ Bảng `homework_teams` và Model `HomeworkTeamModel`

### Decision
- Xóa bỏ bảng `homework_teams` khỏi cơ sở dữ liệu thông qua Alembic migration (`op.drop_table('homework_teams')`).
- Xóa bỏ class `HomeworkTeamModel` trong `app/homework/infrastructure/model.py`.
- Xóa relationship `teams` trong `HomeworkModel`.
- Chuyển 100% việc lưu trữ phân công bài tập sang bảng `homework_assignees` (`HomeworkAssigneeModel`) với trường `assignee_ids`.

### Rationale
- Việc phân công bài tập theo nhóm (Team) được phân giải trực tiếp từ Frontend (UI lấy danh sách `user_ids` thuộc các team được chọn và gửi `assignee_ids` về Backend).
- Giảm thiểu việc phải join 2 bảng (`homework_assignees` và `homework_teams`), giảm thiểu các bug phân giải không nhất quán khi thành viên rời/gia nhập team sau khi bài tập đã giao.
- Đơn giản hóa `HomeworkRepository` và `CheckOverdueHomeworkUseCase`.

### Alternatives Considered
- *Lưu `team_ids` dạng JSON Array trong bảng `homeworks`*: Bị từ chối vì vi phạm chuẩn dữ liệu quan hệ và không cần thiết khi UI đã tự phân giải thành `assignee_ids`.
- *Giữ bảng `homework_teams` nhưng không query*: Bị từ chối vì tạo ra bảng mồ côi (dead table) trong database.

---

## 2. Loại bỏ Toàn Bộ Class & DTO Legacy `HomeworkSubmission`

### Decision
- Xóa class domain entity `HomeworkSubmission` trong `app/homework/domain/entity.py`.
- Xóa thuộc tính `submissions: list[HomeworkSubmission]` trong entity `Homework`.
- Xóa các DTO legacy trong `app/homework/application/dtos.py`:
  - `HomeworkSubmissionCreate`
  - `HomeworkSubmissionUpdate`
  - `HomeworkSubmissionResponse`
  - `HomeworkReportResponse` (nếu không dùng)
- Xóa permission enum `HomeworkSubmissionPermission` trong `app/rbac/domain/value_objects.py` và `app/core/permissions.py` (cùng các script seed liên quan).
- Giữ lại và chuẩn hóa flow kiểm tra trạng thái nộp bài thời gian thực qua Quiz API: `GetHomeworkSubmissionStatusUseCase` và `HomeworkSubmissionStatusResponse`.

### Rationale
- Hệ thống đã chuyển đổi hoàn toàn sang việc đối soát nộp bài Coding / Game qua Quiz API. Bảng `homework_submissions` vật lý trong database đã được drop từ migration trước.
- Các class và DTO submission cũ trong code là nợ kỹ thuật (dead code) gây nhầm lẫn.

---

## 3. Gỡ Bỏ Phụ Thuộc Vào `TeamRepository` trong Domain Homework

### Decision
- `CheckOverdueHomeworkUseCase` và `RescanAllHomeworksUseCase` sẽ chỉ cần `HomeworkRepository`, `QuizApiClient`, `UserRepository`, `EventBus`.
- Gỡ bỏ tham số `team_repo: TeamRepository` khỏi các use case và constructor của `HomeworkUseCases` trong DI container (`app/homework/providers.py`).

### Rationale
- Khi không còn `team_ids` trong Homework, việc kiểm tra hạn nộp bài chỉ cần duyệt qua `assignee_ids` của bài tập và tra cứu tiến độ với Quiz API. Không cần inject `TeamRepository` vào domain Homework nữa.

---

## 4. Tách Nhỏ Use Cases (Single Responsibility Principle)

### Decision
- Tách các file gom (`crud_use_cases.py`, `checker_use_cases.py`, `submission_use_cases.py`, `use_cases.py`) thành các file đơn lập:
  - `app/homework/application/create_homework_use_case.py`
  - `app/homework/application/get_homeworks_use_case.py`
  - `app/homework/application/update_homework_use_case.py`
  - `app/homework/application/delete_homework_use_case.py`
  - `app/homework/application/get_homework_submission_status_use_case.py`
  - `app/homework/application/check_overdue_homework_use_case.py`
  - `app/homework/application/rescan_all_homeworks_use_case.py`
  - `app/homework/application/__init__.py` (re-export)

### Rationale
- Đồng nhất chuẩn kiến trúc Clean Architecture trên toàn bộ hệ thống (như domain `Meeting` và `Violation`).
- Dễ dàng unit test, mock dependencies và loại bỏ hoàn toàn các lỗi typecheck / circular imports.
