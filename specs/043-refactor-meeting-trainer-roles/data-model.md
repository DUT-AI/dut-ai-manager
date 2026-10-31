# Data Model: Phân Loại Vai Trò Trainer & Trainee Trong Buổi Học

**Feature**: `043-refactor-meeting-trainer-roles`  
**Date**: 2026-11-01  

---

## 1. Domain Entities & Value Objects

### 1.1 `ParticipantRole` (Value Object Enum)
```python
class ParticipantRole(StrEnum):
    TRAINER = "TRAINER"  # Người hướng dẫn / Giảng viên / Chủ trì buổi sinh hoạt
    TRAINEE = "TRAINEE"  # Học viên tham dự
```

### 1.2 `MeetingParticipant` (Entity)
Đại diện cho một thành viên tham gia buổi học:

| Trường | Kiểu dữ liệu | Mặc định | Mô tả |
| :--- | :--- | :--- | :--- |
| `id` | `int` | Auto | Khóa chính |
| `meeting_id` | `int` | Bắt buộc | ID buổi học |
| `user_id` | `int` | Bắt buộc | ID người dùng |
| `role` | `ParticipantRole` | `TRAINEE` | Vai trò trong buổi học (`TRAINER` hoặc `TRAINEE`) |
| `status` | `ParticipantStatus` | `NOT_JOINED` | Trạng thái tham gia (7 trạng thái) |
| `check_in_at` | `datetime \| None` | `None` | Thời điểm điểm danh (UTC) |
| `check_out_at` | `datetime \| None` | `None` | Thời điểm checkout (UTC) |
| `link_image` | `str \| None` | `None` | Ảnh bằng chứng điểm danh |
| `client_event_id`| `str \| None` | `None` | Khóa idempotency checkin |
| `user` | `UserRef \| None` | `None` | Thông tin người dùng snapshot |

---

## 2. Database Schema (`meeting_participants`)

```sql
-- 1. Thêm cột role vào bảng meeting_participants
ALTER TABLE meeting_participants 
ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'TRAINEE';

-- 2. Tạo index cho cột role phục vụ lọc Trainer/Trainee
CREATE INDEX ix_meeting_participants_role ON meeting_participants (role);
CREATE INDEX ix_meeting_participants_meeting_role ON meeting_participants (meeting_id, role);

-- 3. Migration dữ liệu lịch sử (CHUẨN HÓA 100%, KHÔNG DÙNG FALLBACK):
-- Cập nhật bản ghi đã tồn tại của created_by thành TRAINER
UPDATE meeting_participants mp
SET role = 'TRAINER'
FROM meetings m
WHERE mp.meeting_id = m.id AND mp.user_id = m.created_by;

-- Chèn thêm 1 dòng Trainer cho created_by nếu chưa có trong danh sách participants của meeting đó
INSERT INTO meeting_participants (
    meeting_id, user_id, role, status, check_in_at, created_at, updated_at
)
SELECT 
    m.id, 
    m.created_by, 
    'TRAINER', 
    'JOINED', 
    m.start_time, 
    COALESCE(m.created_at, NOW()), 
    COALESCE(m.created_at, NOW())
FROM meetings m
WHERE m.created_by IS NOT NULL
  AND NOT EXISTS (
      SELECT 1 FROM meeting_participants mp 
      WHERE mp.meeting_id = m.id AND mp.user_id = m.created_by
  );
```

---

## 3. Data Transfer Objects (DTOs)

### 3.1 `MeetingCreate`
```python
class MeetingCreate(BaseModel):
    title: str
    content: str | None = None
    start_time: UtcDateTime
    end_time: UtcDateTime
    require_check_in: bool = True
    enable_evaluation: bool = False
    trainer_ids: list[int] = Field(default_factory=list, description="Danh sách ID Trainer")
    trainee_ids: list[int] = Field(default_factory=list, description="Danh sách ID Trainee")
    # KHÔNG CÓ FALLBACK: Tuyệt đối không fallback qua user_ids hay created_by
```

### 3.2 `MeetingUpdate`
```python
class MeetingUpdate(BaseModel):
    title: str | None = None
    content: str | None = None
    start_time: UtcDateTime | None = None
    end_time: UtcDateTime | None = None
    require_check_in: bool | None = None
    enable_evaluation: bool | None = None
    trainer_ids: list[int] | None = None
    trainee_ids: list[int] | None = None
    # KHÔNG CÓ FALLBACK: Tuyệt đối không fallback qua user_ids
```

### 3.3 `ParticipantResponse`
```python
class ParticipantResponse(BaseModel):
    id: int
    meeting_id: int
    user_id: int
    role: ParticipantRole = ParticipantRole.TRAINEE
    status: ParticipantStatus
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    user_name: str | None = None
    user_avatar_url: str | None = None
    user_email: str | None = None
```

### 3.4 `MeetingResponse`
```python
class MeetingResponse(BaseModel):
    id: int
    title: str
    content: str | None = None
    start_time: datetime
    end_time: datetime
    require_check_in: bool
    enable_evaluation: bool
    evaluation_deadline: datetime | None = None
    created_by: int | None = None
    trainers: list[UserRefDto] = []             # Danh sách tất cả các Trainer bình đẳng
    trainer: UserRefDto | None = None          # Deprecated backward compatibility (nếu có 1 trainer thì gán, không thì None)
    participants: list[ParticipantResponse] = []
```

---

## 4. UI Component Architecture (Tách 2 Bảng Riêng Biệt)

```text
MeetingParticipantsTab
├── MeetingBatchCheckInBanner (Điểm danh nhanh)
├── TraineeEvaluationCard (Học viên tự đánh giá Trainer - có dropdown chọn Trainer nếu nhiều)
├── EvaluationProgressFilterBar (Bộ lọc tiến độ đánh giá - gắn với Bảng Trainee)
├── TrainerSection
│   ├── Header: "Giảng viên / Phụ trách ({trainers.length})"
│   └── TrainerListTable (Bảng riêng cho Trainer)
│       └── Columns: Giảng viên, Trạng thái tham gia, Check-in, Check-out, Ảnh quẹt thẻ, Điểm đánh giá TB
└── TraineeSection
    ├── Header: "Danh sách Học viên ({trainees.length})"
    └── TraineeListTable (Bảng riêng cho Trainee)
        └── Columns: Học viên, Trạng thái tham gia, Check-in, Check-out, Đánh giá Trainer, Ảnh quẹt thẻ, Thao tác (Đổi trạng thái, Đánh giá học viên)
```
