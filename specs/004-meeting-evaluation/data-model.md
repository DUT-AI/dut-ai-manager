# Phase 1 Data Model: Đánh Giá 2 Chiều Cá Nhân (Trainer & Trainee)

## 1. Entity Relationship Diagram (ERD)

```text
+-------------------+            +-----------------------------------+
|      Meeting      | 1        * |         MeetingEvaluation         |
+-------------------+------------+-----------------------------------+
| id (PK)           |            | id (PK)                           |
| title             |            | meeting_id (FK -> meetings.id)    |
| start_time        |            | reviewer_id (FK -> users.id)      |
| end_time          |            | target_user_id (FK -> users.id)   |
| enable_evaluation |            | evaluation_type (ENUM)            |
| ...               |            | is_anonymous (BOOLEAN)            |
+-------------------+            | scores (JSONB / list of criteria) |
                                 | average_score (FLOAT)             |
                                 | feedback_text (TEXT)              |
                                 | created_at, updated_at            |
                                 +-----------------------------------+
```

---

## 2. Chi tiết Thuộc tính và Ràng buộc Bảng (SQL Schema)

### A. Mở rộng bảng `meetings`:
- `enable_evaluation`: `BOOLEAN DEFAULT FALSE` — Bật/tắt tính năng đánh giá 2 chiều.
- `evaluation_deadline`: `TIMESTAMP NULL` — Mốc thời gian chốt đánh giá (tính bằng `end_time + INTERVAL '24 hours'`).

### B. Bảng `meeting_evaluations`:
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY, AUTO_INCREMENT` | Định danh bản ghi đánh giá |
| `meeting_id` | `INTEGER` | `FOREIGN KEY (meetings.id), INDEX, NOT NULL` | Buổi học/Meeting diễn ra hoạt động đánh giá |
| `reviewer_id` | `INTEGER` | `FOREIGN KEY (users.id), INDEX, NOT NULL` | Người thực hiện đánh giá (**luôn lưu ID thực tế trong DB** dù có chọn ẩn danh) |
| `target_user_id` | `INTEGER` | `FOREIGN KEY (users.id), INDEX, NOT NULL` | **Cá nhân được nhận đánh giá** (Trainer hoặc Trainee cụ thể) |
| `evaluation_type` | `VARCHAR(50)` | `NOT NULL` | Enum: `TRAINER_TO_TRAINEE` hoặc `TRAINEE_TO_TRAINER` |
| `is_anonymous` | `BOOLEAN` | `DEFAULT FALSE, NOT NULL` | Cờ ẩn danh (khi `True`, API trả về cho người dùng sẽ mask/giấu thông tin `reviewer`) |
| `scores` | `JSONB` | `NOT NULL` | Danh sách điểm tiêu chí: `[{"criteria_code": "...", "score": 5}]` (1-5 sao) |
| `average_score` | `FLOAT` | `NOT NULL` | Điểm trung bình cộng của các tiêu chí |
| `feedback_text` | `VARCHAR(2000)` | `NULLABLE` | Lời nhận xét, góp ý cá nhân |
| `created_at` | `TIMESTAMP` | `NOT NULL` | Thời gian gửi đánh giá |
| `updated_at` | `TIMESTAMP` | `NOT NULL` | Thời gian cập nhật |

#### Unique Index / Idempotency Constraint:
- `uq_meeting_evaluation`: `UNIQUE(meeting_id, reviewer_id, target_user_id)` — Mỗi người chỉ được đánh giá 1 lần duy nhất cho một đối tượng cá nhân trong cùng một buổi học.

---

## 3. Domain Model (Pydantic / Clean Architecture)

### Domain Entities:
```python
from enum import Enum
from pydantic import BaseModel
from app.shared.domain.base_entity import BaseEntity
from app.meeting.domain.entity import UserRef

class EvaluationType(str, Enum):
    TRAINER_TO_TRAINEE = "TRAINER_TO_TRAINEE"
    TRAINEE_TO_TRAINER = "TRAINEE_TO_TRAINER"

class EvaluationScoreItem(BaseModel):
    criteria_code: str
    score: int  # 1 to 5

class MeetingEvaluation(BaseEntity):
    meeting_id: int
    reviewer_id: int                     # Luôn lưu ID thực của người đánh giá trong DB
    target_user_id: int                  # Luôn trỏ tới 1 cá nhân cụ thể (Trainer hoặc Trainee)
    evaluation_type: EvaluationType
    is_anonymous: bool = False           # Nếu True, che giấu danh tính người đánh giá ở tầng hiển thị
    scores: list[EvaluationScoreItem]
    average_score: float
    feedback_text: str | None = None
    reviewer: UserRef | None = None      # Thông tin hiển thị (bị None/Mask khi is_anonymous=True)
    target_user: UserRef | None = None   # Thông tin người được đánh giá

    def calculate_average(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.score for s in self.scores) / len(self.scores), 2)
```

---

## 4. Cơ chế Bảo mật Danh tính & Ẩn danh (Privacy Protocol)

1. **Tại tầng Lưu trữ (Database / Infrastructure)**:
   - `reviewer_id` **luôn luôn được lưu trữ chính xác** vào Database để đảm bảo tính toàn vẹn dữ liệu, phục vụ kiểm soát chống đánh giá trùng lặp (`UNIQUE(meeting_id, reviewer_id, target_user_id)`) và tự động kiểm tra hạn chót 24h để tạo `Violation`.
2. **Tại tầng Trình bày / API (Presentation & API)**:
   - Khi Trainer xem đánh giá mà Trainee gửi cho mình: Nếu bản ghi có `is_anonymous = True`, DTO/Schema trả về sẽ đặt `reviewer = null` và thay tên người gửi thành `"Học viên ẩn danh"`.
   - Trainee khác tuyệt đối không thể xem phiếu đánh giá của nhau.

---

## 5. State Lifecycle & Transitions

```text
[Buổi học tạo: enable_evaluation=True]
                │
                ▼ (Khi start_time <= now <= end_time)
         [Buổi học Đang diễn ra]
                │
                ▼ (Khi now > end_time)
    [Mở luồng đánh giá cá nhân trong 24h]
       │                                  │
       ▼                                  ▼
[Trainer đánh giá từng Trainee]     [Trainee đánh giá Trainer]
 (target_user_id = trainee_id)       (target_user_id = trainer_id)
       │                                  │
       └────────────────┬─────────────────┘
                        ▼
            (Sau 24h kết thúc buổi học)
                        │
            ┌───────────┴───────────┐
            ▼                       ▼
     [Đã nộp đủ]           [Chưa nộp sau 24h]
            │                       │
      [Hoàn tất]          [Tự động tạo VIOLATION]
```
