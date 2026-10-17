# Data Model: Tách Biệt Use Case Homework & Dọn Dẹp Code Rác (014-homework-modular-use-cases)

Đợt tái cấu trúc này là **pure refactoring** ở tầng Application và Infrastructure cleanup, **không thay đổi cấu trúc bảng cơ sở dữ liệu** và **không thay đổi Domain Entities / DTOs**.

## 1. Domain Entities & Value Objects (Giữ nguyên)
- `Homework`: Entity bài tập (`title`, `deadline`, `link`, `slug`, `requires_coding`, `requires_game`, `assignee_ids`).
- `HomeworkSubmission`: Entity bài nộp (`homework_id`, `user_id`, `submission_type`, `submitted_at`, `is_passed`, `score`, `details`).

## 2. DTOs (Giữ nguyên)
- `HomeworkResponse`: DTO trả về cho client kèm cờ `is_submitted`, `is_overdue`, `coding_submitted`, `game_submitted`, `uncompleted_items`.
- `HomeworkReportResponse`: DTO thống kê user và `unsubmitted_count`.

## 3. Use Case Architecture Mapping (Mới)

```text
[HTTP Router: /homeworks] ──> GetHomeworksPagedUseCase.execute(...) ──> HomeworkRepository.get_paged(...)
[HTTP Router: /homeworks/{id}] ──> GetHomeworkDetailUseCase.execute(...) ──> HomeworkRepository.get_by_id(...)
[HTTP Router: /homeworks/me] ──> GetUserHomeworksUseCase.execute(...) ──> HomeworkRepository.get_user_submissions_for_homeworks(...)
[HTTP Router: /homeworks/report/unsubmitted/{uid}] ──> GetUnsubmittedHomeworksForUserUseCase.execute(...) ──> HomeworkRepository.get_user_submissions_for_homeworks(...)
[HTTP Router: /homeworks/report/unsubmitted] ──> GetUnsubmittedHomeworkReportUseCase.execute(...) ──> HomeworkRepository.get_all_submissions(...) & UserRepository.get_active_users(...)
```
