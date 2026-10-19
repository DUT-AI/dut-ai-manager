# Research & Design Decisions: Loại Bỏ `assignee_ids` Khỏi Entity `Homework`

## 1. Context & Problem Statement
Thực thể `Homework` (Aggregate Root) trong `backend/app/homework/domain/entity.py` đang chứa thuộc tính `assignee_ids: list[int] = []`.
Điều này gây ra:
- **Vi phạm ranh giới Aggregate Root**: `Homework` phải gánh vác danh sách ID học sinh trong quan hệ Many-to-Many.
- **Lãng phí tài nguyên**: Mỗi lần load `Homework` đều phải query bảng `homework_assignees` để nạp danh sách IDs.
- **Trách nhiệm chồng chéo**: Việc phân công học viên thực chất đã có `HomeworkAssigneeRepository` quản lý độc lập.

## 2. Research Decisions

### Decision 1: Domain Entity `Homework`
- **Quyết định**: Xóa hoàn toàn `assignee_ids` khỏi `Homework(BaseEntity)`.
- **Lý do**: `Homework` chỉ nên đại diện cho đề bài tập với các thuộc tính: `id`, `title`, `deadline`, `link`, `slug`, `requires_coding`, `requires_game`.
- **Phương án khác cân nhắc**: Giữ `assignee_ids: list[int] | None = None` -> Bị loại bỏ vì không giải quyết dứt điểm ranh giới Aggregate Root.

### Decision 2: Tách biệt Write Operations trong Use Cases
- **Quyết định**: 
  - `CreateHomeworkUseCase`: Tạo `Homework` bằng `homework_repo.create(homework)`. Sau đó gọi `homework_assignee_repo.sync_assignees(created.id, data.assignee_ids)` nếu có `assignee_ids`.
  - `UpdateHomeworkUseCase`: Cập nhật `Homework` qua `homework_repo.update(homework)`. Sau đó gọi `homework_assignee_repo.sync_assignees(homework_id, data.assignee_ids)` nếu `data.assignee_ids is not None`.
- **Lý do**: Tách biệt rõ ràng việc quản lý đề bài tập và việc phân công học sinh.
- **Lợi ích**: `HomeworkRepository.create()` và `update()` không còn phụ thuộc vào `HomeworkAssigneeModel` hay `sync_assignees`.

### Decision 3: Tách biệt Read Operations trong Use Cases
- **Quyết định**:
  - `CheckOverdueHomeworkUseCase`: Thay `assigned_uids = set(homework.assignee_ids or [])` bằng `self.homework_assignee_repo.get_assigned_user_ids(homework.id)`.
  - `GetUnsubmittedHomeworkReportUseCase`: Sử dụng `self.homework_assignee_repo.get_assigned_user_ids(hw.id)` hoặc query trực tiếp để lọc thay vì duyệt `hw.assignee_ids`.
  - `GetUserHomeworksUseCase`: Sử dụng `self.homework_repo.get_all_assigned_to_user(user_id)` và map DTO với `assignee_ids=[]` hoặc lấy danh sách assignees nếu cần.
- **Lý do**: Sử dụng đúng repository chuyên trách, không gọi thuộc tính không tồn tại trên entity.

### Decision 4: Infrastructure Model & Repository Cleanup
- **Quyết định**:
  - `HomeworkModel.to_entity()` không còn trả về `assignee_ids`.
  - `HomeworkRepository` xóa hàm `sync_assignees` và logic insert `HomeworkAssigneeModel` trong `create()`. Mọi trách nhiệm này đã nằm trong `HomeworkAssigneeRepository`.
- **Lý do**: Tuân thủ Single Responsibility Principle (SRP).
