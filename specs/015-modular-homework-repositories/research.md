# Phase 0: Research & Technical Decisions

## Decision 1: Phân rã Repository theo đúng ranh giới thực thể (DDD Single Responsibility)

- **Context**: Tệp `backend/app/homework/infrastructure/repository.py` hiện tại gồm 405 dòng code, chứa 1 class duy nhất `HomeworkRepository` nhưng thao tác trên 3 bảng cơ sở dữ liệu khác nhau: `homeworks`, `homework_submissions`, và `homework_assignees`.
- **Decision**: Tách thành 3 class độc lập nằm trong 3 file riêng biệt:
  1. `HomeworkRepository` trong `backend/app/homework/infrastructure/homework_repository.py`:
     - Chuyên trách bảng `homeworks` (`HomeworkModel`).
     - Quản lý CRUD bài tập, phân trang bài tập, tìm theo slug, soft delete, restore.
     - Cung cấp method truy vấn bài tập được giao cho user: `get_assigned_to_user_paged(user_id, page, page_size, deleted)` và `get_all_assigned_to_user(user_id, deleted)`.
  2. `HomeworkSubmissionRepository` trong `backend/app/homework/infrastructure/homework_submission_repository.py`:
     - Chuyên trách bảng `homework_submissions` (`HomeworkSubmissionModel`).
     - Quản lý thêm bài nộp, lấy lịch sử nộp bài của user, lấy bài nộp cho danh sách bài tập (`get_user_submissions_for_homeworks`), lấy tất cả bài nộp (`get_all_submissions`), kiểm tra tính hợp lệ (`has_valid_submission`), tìm bài nộp khớp (`find_submission_match`), cập nhật bài nộp (`update_submission`), lấy exercise ids đã nộp (`get_submitted_exercise_ids`).
  3. `HomeworkAssigneeRepository` trong `backend/app/homework/infrastructure/homework_assignee_repository.py`:
     - Chuyên trách bảng `homework_assignees` (`HomeworkAssigneeModel`).
     - Quản lý đồng bộ phân công (`sync_assignees`), lấy danh sách user_id được giao (`get_assigned_user_ids`), lấy danh sách homework_id của một user (`get_assigned_homework_ids`), thêm/xóa assignee.
- **Rationale**: 
  - Tuân thủ triệt để Nguyên tắc I (Clean Architecture & Practical DDD Boundaries) và Nguyên tắc VII (Single Responsibility).
  - Tránh God Class / God Repository; mỗi repository chỉ chịu trách nhiệm cho đúng 1 aggregate root / bảng dữ liệu liên kết.
- **Alternatives considered**: 
  - *Giữ nguyên 1 file `repository.py` nhưng tạo 3 class*: Vẫn vi phạm tính modular của file, file dài và khó maintain. Đã bị loại bỏ.

---

## Decision 2: Tối ưu hóa truy vấn bài tập được giao bằng SQL JOIN trực tiếp

- **Context**: 
  - Trong `GetUserHomeworksUseCase`, code cũ gọi `self.homework_repo.get_all(skip=0, limit=1000)` rồi dùng vòng lặp Python `for hw in all_homeworks: if user_id in (hw.assignee_ids or []): ...` và cắt slice phân trang trên RAM `paged_hw = assigned_homeworks[skip:skip+limit]`.
  - Trong `GetUnsubmittedHomeworksForUserUseCase`, code cũ cũng gọi `self.homework_repo.get_all()` rồi lọc `[hw for hw in all_homeworks if hw.id and user_id in (hw.assignee_ids or [])]`.
- **Decision**: 
  - Triển khai phương thức trong `HomeworkRepository`:
    ```python
    def get_assigned_to_user_paged(
        self,
        user_id: int,
        page: int = 1,
        page_size: int = 20,
        deleted: bool = False,
    ) -> tuple[list[HomeworkEntity], int]:
        # Count total
        count_stmt = (
            select(func.count(HomeworkModel.id))
            .join(HomeworkAssigneeModel, HomeworkModel.id == HomeworkAssigneeModel.homework_id)
            .where(
                HomeworkAssigneeModel.user_id == user_id,
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkModel.is_deleted == deleted,
            )
        )
        total = self.session.scalar(count_stmt) or 0
        if total == 0:
            return [], 0

        # Query paged models
        stmt = (
            select(HomeworkModel)
            .join(HomeworkAssigneeModel, HomeworkModel.id == HomeworkAssigneeModel.homework_id)
            .where(
                HomeworkAssigneeModel.user_id == user_id,
                HomeworkAssigneeModel.is_deleted == False,
                HomeworkModel.is_deleted == deleted,
            )
            .order_by(desc(HomeworkModel.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        models = self.session.scalars(stmt).all()
        return [m.to_entity() for m in models], total
    ```
  - Triển khai `get_all_assigned_to_user(self, user_id: int, deleted: bool = False) -> list[HomeworkEntity]` sử dụng SQL JOIN tương tự (không phân trang) cho use case tính unsubmitted homeworks.
- **Rationale**: 
  - Khắc phục triệt để anti-pattern fetch-all in-memory filtering.
  - Tận dụng index trên `HomeworkAssigneeModel.user_id` và `homework_id` giúp truy vấn thực thi trong thời gian $O(\log N)$ tại DB thay vì tốn $O(N)$ CPU & RAM của backend.
  - Phân trang chuẩn xác ở tầng Database với `LIMIT` và `OFFSET`.
- **Alternatives considered**:
  - *Query danh sách homework_ids từ `HomeworkAssigneeRepository` trước rồi query `HomeworkModel.id.in_(ids)`*: Cần 2 round-trips tới database. Phép `JOIN` 1 query duy nhất nhanh và hiệu quả hơn.

---

## Decision 3: Xử lý Backward Compatibility và File Structure

- **Context**: 
  - File cũ `repository.py` được import ở nhiều nơi.
  - Hiến pháp v1.5.0, Nguyên tắc X nghiêm cấm: *"Zero Redundant Backward Compatibility & No Duplicate API Surface: Never create redundant re-exports or aliases merely to avoid updating callers. Refactor call sites directly."*
- **Decision**: 
  - Cập nhật trực tiếp tất cả call sites (các use case, dishka provider, controller, test).
  - Không giữ lại file `repository.py` hay tạo alias re-export từ `repository.py`.
  - Tạo file `backend/app/homework/infrastructure/__init__.py` chỉ để export các class canonical:
    ```python
    from app.homework.infrastructure.homework_repository import HomeworkRepository
    from app.homework.infrastructure.homework_submission_repository import HomeworkSubmissionRepository
    from app.homework.infrastructure.homework_assignee_repository import HomeworkAssigneeRepository

    __all__ = [
        "HomeworkRepository",
        "HomeworkSubmissionRepository",
        "HomeworkAssigneeRepository",
    ]
    ```
  - Xóa bỏ file `backend/app/homework/infrastructure/repository.py`.
- **Rationale**:
  - Tuân thủ tuyệt đối Constitution v1.5.0 Nguyên tắc X.
  - Giữ codebase sạch sẽ, không có code thừa thãi.
