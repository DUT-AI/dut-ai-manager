# Research: Tách Biệt Use Case Homework & Dọn Dẹp Code Rác (014-homework-modular-use-cases)

## Quyết Định Kiến Trúc (Architecture Decisions)

### 1. Phân tách `GetHomeworksUseCase` thành 5 Use Case chuyên biệt
- **Context**: `GetHomeworksUseCase` hiện chứa 6 method: `get_paged`, `get_all`, `get_by_id`, `get_assigned_to_user`, `get_unsubmitted_for_user`, `get_unsubmitted_report`.
- **Quyết định**:
  - `GetHomeworksPagedUseCase` (`get_homeworks_paged_use_case.py`): Nhận `(page: int, page_size: int, deleted: bool)` -> `(list[HomeworkEntity], int)`. Inject `HomeworkRepository`.
  - `GetHomeworkDetailUseCase` (`get_homework_detail_use_case.py`): Nhận `(homework_id: int)` -> `HomeworkEntity | None`. Inject `HomeworkRepository`.
  - `GetUserHomeworksUseCase` (`get_user_homeworks_use_case.py`): Nhận `(user_id: int, page: int, page_size: int, skip: int | None, limit: int | None)` -> `(list[HomeworkResponse], int)`. Inject `HomeworkRepository`.
  - `GetUnsubmittedHomeworksForUserUseCase` (`get_unsubmitted_homeworks_for_user_use_case.py`): Nhận `(user_id: int)` -> `list[HomeworkEntity]`. Inject `HomeworkRepository`.
  - `GetUnsubmittedHomeworkReportUseCase` (`get_unsubmitted_homework_report_use_case.py`): Nhận `()` -> `list[HomeworkReportResponse]`. Inject `HomeworkRepository`, `UserRepository`.
- **Rationale**: Mỗi class có chính xác 1 phương thức `execute`, tuân thủ 100% Nguyên tắc VII & IX của Constitution v1.5.0.

### 2. Xử lý mã nguồn rác (Dead Code Elimination)
- **`backend/app/homework/domain/services.py`**: Chứa `class HomeworkService: pass` không logic, không ai import. Quyết định: Xóa file hoặc chuyển đổi thành module hữu ích. Do không có logic dùng chung, tiến hành xóa file để tránh nhầm lẫn.
- **`backend/app/homework/infrastructure/external_api.py`**: Chứa `HomeworkGradingService` gọi HTTP POST đến `settings.SUBMISSION_CHECKER_API_URL`. Toàn bộ backend không có dòng nào import hay gọi class này. Quyết định: Xóa file `external_api.py`.
- **`get_homeworks_use_case.py`**: Sau khi phân tách xong và cập nhật tất cả call sites, xóa hoàn toàn file cũ.

### 3. Cập nhật call sites tại module `report`
- **Context**: `backend/app/report/application/use_cases.py` (class `GetDashboardOverviewUseCase`) đang inject `GetHomeworksUseCase` để gọi `get_unsubmitted_for_user`.
- **Quyết định**: Đổi dependency thành `GetUnsubmittedHomeworksForUserUseCase`. Cập nhật `backend/app/report/providers.py` tương ứng. Không dùng alias backward compatibility.
