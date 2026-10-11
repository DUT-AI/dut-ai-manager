# Phase 1 Data Model: Đánh Giá 2 Chiều Buổi Học (Trainer Đánh Giá Meeting 1-1 & Trainee Đánh Giá Trainer)

## 1. Entity Relationship Diagram (ERD)

```text
                  +-----------------------------------+
                  |     MeetingOverallEvaluation      |
                  +-----------------------------------+
                  | id (PK)                           |
             1    | meeting_id (FK -> meetings.id, UQ)|
           +------+ trainer_id (FK -> users.id)       |
           |      | scores (JSONB)                    |
           |      | average_score (FLOAT)             |
           |      | general_feedback (TEXT)           |
+----------+--------+ | created_at, updated_at            |
|      Meeting      | +-----------------------------------+
+-------------------+
| id (PK)           | 1
| title             | +------+
| start_time        |        |
| end_time          |        | *
| enable_evaluation | +-----------------------------------+
| ...               | |         MeetingEvaluation         |
+-------------------+ +-----------------------------------+
                      | id (PK)                           |
                      | meeting_id (FK -> meetings.id)    |
                      | reviewer_id (FK -> users.id)      |
                      | target_user_id (FK -> users.id)   |
                      | is_anonymous (BOOLEAN)            |
                      | scores (JSONB)                    |
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

### B. Bảng riêng biệt `meeting_overall_evaluations` (Quan hệ 1 - 1 với Meeting):
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY, AUTO_INCREMENT` | Định danh bản ghi |
| `meeting_id` | `INTEGER` | `FOREIGN KEY (meetings.id), UNIQUE, NOT NULL` | Buổi học được đánh giá (quan hệ 1 - 1) |
| `trainer_id` | `INTEGER` | `FOREIGN KEY (users.id), NOT NULL` | Trainer thực hiện đánh giá |
| `scores` | `JSONB` | `NOT NULL` | Danh sách điểm theo 4 tiêu chí: `[{"criteria_code": "...", "score": 5}]` |
| `average_score` | `FLOAT` | `NOT NULL` | Điểm trung bình cộng của 4 tiêu chí |
| `general_feedback` | `VARCHAR(2000)` | `NULLABLE` | Nhận xét chung cho buổi học |
| `created_at` | `TIMESTAMP` | `NOT NULL` | Thời gian gửi đánh giá |
| `updated_at` | `TIMESTAMP` | `NOT NULL` | Thời gian cập nhật |

#### Ràng buộc duy nhất:
- `uq_meeting_overall_evaluation`: `UNIQUE(meeting_id)` — Mỗi buổi học chỉ có duy nhất 1 bản ghi đánh giá tổng thể từ Trainer.

---

### C. Bảng `meeting_evaluations` (Trainee đánh giá Trainer):
| Tên cột | Kiểu dữ liệu | Ràng buộc | Mô tả |
|---|---|---|---|
| `id` | `INTEGER` | `PRIMARY KEY, AUTO_INCREMENT` | Định danh bản ghi |
| `meeting_id` | `INTEGER` | `FOREIGN KEY (meetings.id), INDEX, NOT NULL` | Buổi học diễn ra hoạt động đánh giá |
| `reviewer_id` | `INTEGER` | `FOREIGN KEY (users.id), INDEX, NOT NULL` | Trainee thực hiện đánh giá (**luôn lưu ID thực tế trong DB**) |
| `target_user_id` | `INTEGER` | `FOREIGN KEY (users.id), INDEX, NOT NULL` | Trainer nhận đánh giá |
| `is_anonymous` | `BOOLEAN` | `DEFAULT FALSE, NOT NULL` | Cờ ẩn danh (khi `True`, API trả về cho Trainer sẽ mask/giấu thông tin `reviewer`) |
| `scores` | `JSONB` | `NOT NULL` | Danh sách điểm 4 tiêu chí: `[{"criteria_code": "...", "score": 5}]` |
| `average_score` | `FLOAT` | `NOT NULL` | Điểm trung bình cộng |
| `feedback_text` | `VARCHAR(2000)` | `NULLABLE` | Nhận xét, góp ý cá nhân cho Trainer |
| `created_at` | `TIMESTAMP` | `NOT NULL` | Thời gian gửi đánh giá |
| `updated_at` | `TIMESTAMP` | `NOT NULL` | Thời gian cập nhật |

#### Ràng buộc duy nhất:
- `uq_meeting_trainee_evaluation`: `UNIQUE(meeting_id, reviewer_id, target_user_id)` — Mỗi Trainee chỉ gửi 1 đánh giá cho Trainer trong cùng 1 buổi học.

---

## 3. Domain Model (Pydantic / Clean Architecture)

### Domain Entities:
```python
from pydantic import BaseModel
from app.shared.domain.base_entity import BaseEntity
from app.meeting.domain.entity import UserRef

class EvaluationScoreItem(BaseModel):
    criteria_code: str
    score: int  # 1 to 5

class MeetingOverallEvaluation(BaseEntity):
    meeting_id: int
    trainer_id: int
    scores: list[EvaluationScoreItem]
    average_score: float
    general_feedback: str | None = None
    trainer: UserRef | None = None

    def calculate_average(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.score for s in self.scores) / len(self.scores), 2)

class MeetingEvaluation(BaseEntity):
    meeting_id: int
    reviewer_id: int                     # Luôn lưu ID thực của Trainee trong DB
    target_user_id: int                  # ID của Trainer
    is_anonymous: bool = False           # Nếu True, che giấu danh tính người gửi
    scores: list[EvaluationScoreItem]
    average_score: float
    feedback_text: str | None = None
    reviewer: UserRef | None = None      # Mask thành "Học viên ẩn danh" khi is_anonymous=True
    target_user: UserRef | None = None   # Trainer info

    def calculate_average(self) -> float:
        if not self.scores:
            return 0.0
        return round(sum(s.score for s in self.scores) / len(self.scores), 2)
```

---

## 4. Cơ chế Bảo mật Danh tính & Phân Quyền (Security & Access Control)

1. **Đánh giá tổng thể buổi học (`MeetingOverallEvaluation`)**:
   - Được công khai ngay cho toàn bộ Trainee tham gia meeting xem ngay khi Trainer nộp đánh giá.
2. **Đánh giá cá nhân Trainer (`MeetingEvaluation`)**:
   - `reviewer_id` **luôn luôn được lưu trữ chính xác** vào Database để kiểm soát tính duy nhất và quét hạn chót 24h.
   - Khi Trainer xem báo cáo tổng hợp: Nếu bản ghi có `is_anonymous = True`, DTO trả về mask `reviewer = null` và tên hiển thị là `"Học viên ẩn danh"`.

---

## 5. State Lifecycle & Transitions

```text
[Buổi học tạo: enable_evaluation=True]
                │
                ▼ (Meeting kết thúc)
[Trạng thái: Chờ Đánh Giá (Hạn chót 24h)]
   ├── Trainer nộp đánh giá meeting 1-1 ──────────► [MeetingOverallEvaluation: Hoàn tất]
   │                                                 (Công khai ngay cho toàn bộ Trainee)
   ├── Trainee nộp đánh giá Trainer ──────────────► [MeetingEvaluation: Hoàn tất]
   │
   ▼ (Sau 24h quét tự động)
[Kiểm tra Hạn chót]:
   ├── Trainer CHƯA nộp MeetingOverallEvaluation ──► Tự động tạo 01 Violation cho Trainer
   └── Trainee CHƯA nộp MeetingEvaluation ─────────► Tự động tạo 01 Violation cho Trainee
```
