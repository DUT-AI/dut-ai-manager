# Research: Lược bỏ is_deleted trên các Model không cần thiết

## 1. Bối cảnh & Vấn đề Kỹ thuật
Trước đây, tất cả các ORM Model đều kế thừa `SQLAlchemyTimestampMixin`, dẫn đến việc mọi bảng trong cơ sở dữ liệu đều tự động có cột `is_deleted: bool = False`.
Tại tính năng 059 (`059-uuid-optional-soft-delete`), chúng ta đã tách biệt thành công các Mixin:
- `SQLAlchemyTimestampOnlyMixin` (chỉ có `created_at`, `updated_at`)
- `SQLAlchemyAuditMixin` (chỉ có `created_by`, `updated_by`)
- `SQLAlchemySoftDeleteMixin` (`is_deleted`)
- `SQLAlchemyUuidPrimaryKeyMixin` / `SQLAlchemyIntPrimaryKeyMixin`
- `BaseGenericEntity[TId]` và `SoftDeleteEntityMixin`

Hiện tại, các model sau đây không cần xóa mềm (nên chuyển sang Hard Delete):
1. `Meeting` & `MeetingParticipant`
2. `Homework` & `HomeworkAssignee`
3. `TeamMember` & `Team`
4. `Notification` & `PushSubscription`
5. `Role`, `Permission`, `UserRole`
6. `MonthlyUserStats`, `InvoiceItem`, `CleaningDuty`

## 2. Phân tích Tác động (Impact Analysis)

### 2.1. Domain Layer
- **`Meeting` & `MeetingParticipant`** ([backend/app/meeting/domain/entity.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/meeting/domain/entity.py)):
  - Hiện tại: Kế thừa `BaseEntity` (mặc định trước đây có `is_deleted`).
  - Cập nhật: Không kế thừa `SoftDeleteEntityMixin`.
- **`Homework` & `HomeworkAssignee`** ([backend/app/homework/domain/entity.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/homework/domain/entity.py)):
  - Hiện tại: Kế thừa `BaseEntity`.
  - Cập nhật: Bỏ `is_deleted`.
- **`TeamMember`** ([backend/app/team/domain/entity.py](file:///Users/nguyenhuynh/Documents/dut-ai-manager/backend/app/team/domain/entity.py)):
  - Kế thừa `BaseEntity`. Bỏ `is_deleted`.

### 2.2. Infrastructure Layer (ORM Models)
Thay đổi kế thừa từ `SQLAlchemyTimestampMixin` sang:
- `SQLAlchemyIntPrimaryKeyMixin, SQLAlchemyTimestampOnlyMixin, SQLAlchemyAuditMixin, Base` (cho các bảng cần audit nhưng không cần soft delete như `Meeting`, `Homework`).
- Hoặc đơn giản là mixin composite mới: `SQLAlchemyAuditTimestampMixin` (Timestamp + Audit nhưng KHÔNG có Soft Delete).

### 2.3. Repository Layer
- `BaseRepository` đã được nâng cấp tại Feature 059 để tự động kiểm tra `hasattr(self.model_cls, "is_deleted")`:
  - Nếu model KHÔNG có cột `is_deleted`, `get_all()`, `get_by_id()` sẽ KHÔNG sinh mệnh đề `WHERE is_deleted = false`.
  - Hàm `delete(id)` trên `BaseRepository` sẽ tự động chuyển sang `hard_delete()` nếu model không có soft delete.
  - Các repository con (`MeetingRepository`, `ParticipantRepository`, `HomeworkRepository`) có các câu query tùy biến cần rà soát để bỏ `where(Model.is_deleted.is_(False))` thủ công.

### 2.4. Migration & Xử lý Dữ liệu trên Database (Data Migration)
Trên cơ sở dữ liệu hiện tại, các bảng sau có bản ghi `is_deleted = true`:
- `meetings`: 44 bản ghi
- `meeting_participants`: 64 bản ghi
- `homeworks`: 8 bản ghi
- `team_members`: 19 bản ghi

**Quy trình dọn dẹp trong Migration (`upgrade`)**:
1. Dọn dẹp bản ghi con:
   ```sql
   -- Dọn dẹp meeting_participants của các meeting đã xóa mềm
   DELETE FROM meeting_participants WHERE meeting_id IN (SELECT id FROM meetings WHERE is_deleted = true);
   -- Dọn dẹp các participants đã xóa mềm
   DELETE FROM meeting_participants WHERE is_deleted = true;
   -- Xóa cascade evaluations của các meeting đã xóa mềm
   DELETE FROM meeting_evaluations WHERE meeting_id IN (SELECT id FROM meetings WHERE is_deleted = true);
   DELETE FROM meeting_overall_evaluations WHERE meeting_id IN (SELECT id FROM meetings WHERE is_deleted = true);
   -- Xóa các meeting đã xóa mềm
   DELETE FROM meetings WHERE is_deleted = true;

   -- Dọn dẹp assignees và submissions của các homeworks đã xóa mềm
   DELETE FROM homework_assignees WHERE homework_id IN (SELECT id FROM homeworks WHERE is_deleted = true);
   DELETE FROM homework_submissions WHERE homework_id IN (SELECT id FROM homeworks WHERE is_deleted = true);
   -- Xóa các homeworks đã xóa mềm
   DELETE FROM homeworks WHERE is_deleted = true;

   -- Dọn dẹp team_members đã xóa mềm
   DELETE FROM team_members WHERE is_deleted = true;
   ```
2. Thực hiện `DROP COLUMN is_deleted` trên các bảng:
   `meetings`, `meeting_participants`, `homeworks`, `homework_assignees`, `team_members`, `user_roles`, `notifications`, `push_subscriptions`, `permissions`, `roles`, `teams`, `monthly_user_stats`, `invoice_items`, `cleaning_duties`.

## 3. Quyết định Kiến trúc (Architectural Decision)
Tạo mixin mới trong `backend/app/shared/infrastructure/base_model.py`:
```python
class SQLAlchemyAuditTimestampMixin(SQLAlchemyTimestampOnlyMixin, SQLAlchemyAuditMixin):
    """Timestamp and User Audit mixin WITHOUT soft-delete (for pure hard-delete entities)."""
    pass
```
Các model `Meeting`, `Homework`, `TeamMember`, `CleaningDuty` sẽ kế thừa `SQLAlchemyAuditTimestampMixin, Base`.
Cực kỳ sạch sẽ, tái sử dụng cao và không làm thay đổi các model vẫn cần soft-delete (`Invoice`, `Violation`, `User`, `PermissionRequest`).
