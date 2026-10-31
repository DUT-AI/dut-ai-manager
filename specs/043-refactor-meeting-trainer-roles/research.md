# Research & Technical Decisions: Phân Loại Vai Trò Trainer & Trainee

**Feature**: `043-refactor-meeting-trainer-roles`  
**Date**: 2026-11-01  

---

## 1. Phân Tích Kiến Trúc Hiện Tại vs Kiến Trúc Mục Tiêu

### Hiện trạng:
- Bảng `meetings`: có `created_by` (người tạo meeting).
- Bảng `meeting_participants`: chỉ có `user_id`, `meeting_id`, `check_in_at`, `status`. Tất cả mọi người bị gom chung làm học viên.
- Mọi logic nhận diện Trainer đều viết: `meeting.created_by == current_user.id`!
- Hệ quả: Admin tạo meeting cho Trainer A dạy thì:
  - Trainer A không có quyền điểm danh, không có quyền sửa buổi học, không có quyền nộp đánh giá tổng thể.
  - Trainee đánh giá thì đánh giá nhầm Admin (vì `target_user_id or meeting.created_by`).
  - Scanner nhắc nhở gửi nhầm cho Admin thay vì Trainer A.

### Kiến trúc Mục tiêu:
- Bảng `meetings`: `created_by` giữ nguyên làm **Audit Log** (Ai tạo bản ghi).
- Bảng `meeting_participants`: Thêm cột `role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE'`.
  - Thành viên có `role = 'TRAINER'`: Là người hướng dẫn / giảng viên của meeting. Có toàn quyền điều hành meeting đó.
  - Thành viên có `role = 'TRAINEE'`: Là học viên tham gia học.
- Form Tạo/Sửa meeting:
  - Ô 1: Chọn Trainer (Multi-select hoặc Single-select, lưu với `role = 'TRAINER'`).
  - Ô 2: Chọn Trainee (Chọn theo Team hoặc cá nhân, lưu với `role = 'TRAINEE'`).

---

## 2. Quyết Định Kỹ Thuật (Technical Decisions)

### Quyết định 1: Định nghĩa Enum `ParticipantRole`
- **Vị trí**: `backend/app/meeting/domain/value_objects.py`
  ```python
  class ParticipantRole(StrEnum):
      TRAINER = "TRAINER"
      TRAINEE = "TRAINEE"
  ```
- **Lợi ích**: Kiểu dữ liệu chặt chẽ (Strict Typing), tương thích hoàn hảo cả SQLAlchemy String, Pydantic V2 và Zod ở frontend.

### Quyết định 2: Migration Database Chuẩn Hóa 100% (Không Fallback)
- Thêm cột `role`:
  ```sql
  ALTER TABLE meeting_participants ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE';
  CREATE INDEX ix_meeting_participants_role ON meeting_participants (role);
  CREATE INDEX ix_meeting_participants_meeting_role ON meeting_participants (meeting_id, role);
  ```
- **Chính sách Backfill theo yêu cầu người dùng**:
  - Đối với tất cả meeting hiện có:
    1. Nếu người tạo (`created_by`) đã có bản ghi trong `meeting_participants`: cập nhật `role = 'TRAINER'`.
    2. Nếu người tạo (`created_by`) chưa có bản ghi trong `meeting_participants`: chèn thêm 1 dòng mới với `role = 'TRAINER'`, `status = 'JOINED'`, `check_in_at = meeting.start_time`.
    3. Toàn bộ các thành viên khác giữ vai trò `TRAINEE`.
  - Nhờ việc chuẩn hóa dữ liệu tận gốc trong DB, code Python backend và TypeScript frontend **tuyệt đối không cần bất kỳ fallback nào** (không fallback sang `user_ids`, không fallback sang `created_by`). Mọi truy vấn Trainer đều đọc trực tiếp từ `role == 'TRAINER'`.

### Quyết định 3: Entity `Meeting` đóng vai trò Aggregate Root
- Thêm các tiện ích domain trong `backend/app/meeting/domain/meeting.py`:
  ```python
  @property
  def trainers(self) -> list[MeetingParticipant]:
      return [p for p in self.participants if not p.is_deleted and p.role == ParticipantRole.TRAINER]

  @property
  def trainees(self) -> list[MeetingParticipant]:
      return [p for p in self.participants if not p.is_deleted and p.role == ParticipantRole.TRAINEE]

  def is_trainer(self, user_id: int) -> bool:
      return any(t.user_id == user_id for t in self.trainers)

  def is_trainee(self, user_id: int) -> bool:
      return any(t.user_id == user_id for t in self.trainees)
  ```
  *(Lưu ý: Không tạo khái niệm `primary_trainer` vì hệ thống hỗ trợ nhiều Trainer bình đẳng cùng phụ trách).*

### Quyết định 4: Hợp đồng API `MeetingCreate` & `MeetingUpdate`
- Hỗ trợ cả 2 trường `trainer_ids` và `trainee_ids`:
  ```python
  class MeetingCreate(BaseModel):
      title: str
      content: str | None = None
      start_time: UtcDateTime
      end_time: UtcDateTime
      require_check_in: bool = True
      enable_evaluation: bool = False
      trainer_ids: list[int] = Field(default_factory=list, description="Danh sách Trainer")
      trainee_ids: list[int] = Field(default_factory=list, description="Danh sách Trainee")
      # KHÔNG CÓ FALLBACK: Tuyệt đối không fallback sang user_ids
  ```
- **Xử lý trùng lặp**: Nếu một user có mặt trong cả `trainer_ids` và `trainee_ids`, hệ thống tự động ưu tiên gán làm `TRAINER` và loại khỏi `trainee_ids`.
- **Hỗ trợ Meeting tự học nhóm (Không có Trainer)**:
  - Cho phép `trainer_ids = []`. Khi đó toàn bộ thành viên đều mang vai trò `TRAINEE`.
  - Quyền điều hành buổi họp thuộc về người tạo (`created_by`) hoặc Admin/Leader.
  - Tự động bỏ qua việc quét nhắc nhở/phạt Trainer (vì không có Trainer nào phụ trách).
  - Học viên không cần đánh giá Trainer.

### Quyết định 5: Nâng cấp Phân Quyền (Authorization)
- Trong `backend/app/meeting/controllers/dependencies.py`:
  - `check_meeting_ownership`:
    Cho phép nếu `current_user` là Admin/Leader **HOẶC** `meeting.created_by == current_user.id` **HOẶC** `meeting.is_trainer(current_user.id)`!
  - `check_meeting_evaluation_permission`:
    Cho phép nếu `current_user` là Admin/Leader **HOẶC** `meeting.is_trainer(current_user.id)` **HOẶC** `meeting.created_by == current_user.id`.

### Quyết định 6: Giao diện Frontend Phân Tách 2 Bảng và 2 Ô Chọn
- **Modal Tạo/Sửa (`MeetingModal.tsx`)**:
  - Tách khu vực phân công thành 2 ô chọn rõ ràng:
    1. **Trainer(s) phụ trách** (`trainer_ids`): Cho phép chọn nhiều Trainer hoặc để trống nếu là tự học nhóm, tag màu vàng `gold`.
    2. **Học viên tham gia (Trainees)** (`trainee_ids`): Cho phép chọn theo Team hoặc cá nhân, tag màu xanh `blue`.
- **Chi tiết Buổi học (`MeetingParticipantsTab.tsx` & `ParticipantListModal.tsx`)**:
  - **Tách làm 2 bảng riêng biệt**:
    1. **Bảng Trainer (`TrainerListTable`)**:
       - Hiển thị danh sách các Trainer phụ trách buổi học.
       - Cột: Giảng viên, Trạng thái tham gia, Check-in, Check-out, Ảnh quẹt thẻ, Điểm đánh giá TB.
       - Không có nút chấm điểm học viên.
    2. **Bảng Trainee (`TraineeListTable`)**:
       - Hiển thị danh sách Học viên tham gia.
       - Cột: Học viên, Trạng thái tham gia, Check-in, Check-out, Trạng thái đánh giá Trainer, Ảnh quẹt thẻ, Thao tác (Điểm danh/Đổi trạng thái, Nút Đánh giá học viên).
- **Modal Học viên Đánh giá Trainer (`TraineeEvaluationModal.tsx`)**:
  - Khi meeting có nhiều Trainer: Cung cấp Radio/Select để học viên chọn Trainer muốn đánh giá. Trainee có thể đánh giá từng Trainer phụ trách.
  - Khi meeting không có Trainer: Ẩn nút/banner nhắc đánh giá Trainer.
