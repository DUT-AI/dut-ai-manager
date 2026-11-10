# Quickstart: Lược bỏ is_deleted trên các Model không cần thiết

## 1. Kiểm tra Môi trường & Chạy Test Hiện tại
```bash
cd backend
uv run pytest tests/unit/
```

## 2. Các bước Thực hiện (Execution Steps)

### Bước 1: Bổ sung Mixin mới trong Base Model
Trong `backend/app/shared/infrastructure/base_model.py`:
Định nghĩa `SQLAlchemyAuditTimestampMixin(SQLAlchemyTimestampOnlyMixin, SQLAlchemyAuditMixin)` không có soft delete.

### Bước 2: Cập nhật các Model sang Hard-Delete
Thay đổi kế thừa của:
- `backend/app/meeting/infrastructure/model.py` (`Meeting`, `MeetingParticipant`, `MeetingEvaluation`, `MeetingOverallEvaluation`)
- `backend/app/homework/infrastructure/model.py` (`HomeworkModel`, `HomeworkAssigneeModel`)
- `backend/app/team/infrastructure/model.py` (`TeamModel`, `TeamMemberModel`)
- `backend/app/reminder/infrastructure/model.py` (`NotificationModel`, `PushSubscriptionModel`)
- `backend/app/duty/infrastructure/model.py` (`CleaningDutyModel`)
- `backend/app/billing/infrastructure/model.py` (`InvoiceItemModel`)
- `backend/app/rbac/infrastructure/model.py` (`RoleModel`, `PermissionModel`, `UserRoleModel`)
- `backend/app/user/infrastructure/model.py` (`MonthlyUserStatsModel`)

### Bước 3: Rà soát & Tối ưu Repository
Rà soát các truy vấn thủ công có `where(Model.is_deleted.is_(False))` trong:
- `MeetingRepository`
- `ParticipantRepository`
- `HomeworkRepository`
- `TeamMemberRepository`
Loại bỏ điều kiện này vì bảng không còn cột `is_deleted`.

### Bước 4: Chạy Migration Dọn dẹp Database
Tạo migration Alembic mới:
1. Dọn sạch các bản ghi `is_deleted = true` lịch sử của 4 bảng (`meetings`, `meeting_participants`, `homeworks`, `team_members`).
2. Thực hiện `DROP COLUMN is_deleted` trên các bảng thuộc diện loại bỏ.
3. Chạy lệnh:
   ```bash
   cd backend
   uv run alembic upgrade head
   ```

### Bước 5: Kiểm tra Toàn bộ Test Suite
```bash
cd backend
uv run pytest
```
