# Data Model: Cho phép người tạo buổi sinh hoạt đánh giá buổi học

**Feature**: `026-fix-creator-meeting-evaluation`  
**Date**: 2026-10-24  
**Status**: Completed  

---

## 1. Domain Entities & Value Objects

### 1.1. `Meeting` (Aggregate Root)
- **Vị trí**: `backend/app/meeting/domain/entity.py`
- **Kế thừa**: `BaseEntity` (đã có sẵn `id`, `created_at`, `updated_at`, `created_by`, `updated_by`, `is_deleted`).
- **Thuộc tính liên quan**:
  ```python
  class Meeting(BaseEntity):
      title: str
      start_time: datetime
      end_time: datetime
      content: str | None = None
      require_check_in: bool = True
      enable_evaluation: bool = False
      participants: list[MeetingParticipant] = Field(default_factory=list)
      creator: UserRef | None = None
      # Kế thừa từ BaseEntity:
      # created_by: int | None = None
  ```
- **Business Methods**:
  - `is_evaluation_open(current_time: datetime) -> tuple[bool, str]`: Kiểm tra cổng đánh giá mở khi buổi học đã bắt đầu và `enable_evaluation=True`.
  - `is_evaluation_expired(current_time: datetime) -> bool`: Kiểm tra hạn chót 24h sau khi kết thúc buổi học.

### 1.2. `UserRef` (Value Object snapshot)
- **Thuộc tính**:
  - `id: int`: Mã người dùng.
  - `name: str`: Họ và tên hoặc tên hiển thị.
  - `avatar_url: str | None`: Đường dẫn ảnh đại diện.

---

## 2. Database Model & Mapping (Infrastructure Layer)

### 2.1. Bảng `meetings`
- **Model**: `Meeting` (`backend/app/meeting/infrastructure/model.py`)
- **Cấu trúc trường**:
  - `id`: `INTEGER` (PK, autoincrement).
  - `title`: `VARCHAR(255)`.
  - `content`: `VARCHAR(1000)`.
  - `start_time`: `TIMESTAMP`.
  - `end_time`: `TIMESTAMP`.
  - `require_check_in`: `BOOLEAN`.
  - `enable_evaluation`: `BOOLEAN`.
  - `evaluation_deadline`: `TIMESTAMP`.
  - `created_by`: `INTEGER` (FK `users.id`, nullable).
  - `updated_by`: `INTEGER` (FK `users.id`, nullable).
  - `created_at`: `TIMESTAMP`.
  - `updated_at`: `TIMESTAMP`.
  - `is_deleted`: `BOOLEAN`.

### 2.2. ORM Mapping Discipline
- Trong `Meeting.to_entity()`:
  - Đảm bảo `created_by=self.created_by` luôn được truyền sang `MeetingEntity`.
  - Đảm bảo `creator=creator_ref` được trích xuất từ relationship `self.creator` hoặc fallback tạo `UserRef(id=self.created_by, name=f"Trainer #{self.created_by}")`.
- Trong `MeetingRepository.save(domain)`:
  - Khi tạo mới `ORMMeeting`: gán `orm.created_by = domain.created_by`.
  - Khi cập nhật `ORMMeeting`: duy trì `orm.created_by` không bị ghi đè thành `None`.

---

## 3. Data Transfer Objects (DTO) / Presentation Schemas

### 3.1. `MeetingResponse` & `MeetingDetailResponse`
- **Vị trí**: `backend/app/meeting/schemas.py`
- **Cập nhật thêm**: Trường `created_by: int | None = None`.
  ```python
  class MeetingResponse(BaseModel):
      model_config = ConfigDict(from_attributes=True)

      id: int
      title: str
      content: str | None = None
      start_time: datetime
      end_time: datetime
      require_check_in: bool
      enable_evaluation: bool = False
      evaluation_deadline: datetime | None = None
      created_by: int | None = None  # <-- BỔ SUNG TRƯỜNG NÀY
      trainer: UserRefDto | None = None
      created_at: datetime
      updated_at: datetime

      @classmethod
      def from_domain(cls, m: "DomainMeeting") -> "MeetingResponse":
          ...
          return cls(
              id=m.id,
              title=m.title,
              content=m.content,
              start_time=m.start_time,
              end_time=m.end_time,
              require_check_in=m.require_check_in,
              enable_evaluation=m.enable_evaluation if m.enable_evaluation is not None else False,
              evaluation_deadline=m.evaluation_deadline,
              created_by=m.created_by,  # <-- MAP GIÁ TRỊ TỪ DOMAIN
              trainer=trainer_dto,
              created_at=m.created_at,
              updated_at=m.updated_at,
          )
  ```

### 3.2. Frontend Schema Alignment
- **Vị trí**: `frontend/src/features/meeting/types/meeting.types.ts`
- Schema Zod đã có sẵn:
  ```typescript
  export const meetingResponseSchema = z.object({
    id: z.number(),
    title: z.string(),
    content: z.string().optional(),
    start_time: z.string(),
    end_time: z.string(),
    require_check_in: z.boolean(),
    enable_evaluation: z.boolean().default(false),
    evaluation_deadline: z.string().nullable().optional(),
    created_by: z.number().nullable().optional(), // ĐÃ CÓ TRƯỚC ĐÓ, CHỈ CẦN BACKEND TRẢ DỮ LIỆU
    trainer: userRefSchema.default({ id: 0, name: 'Trainer' }),
    created_at: z.string(),
    updated_at: z.string(),
  });
  ```

---

## 4. State & Evaluation Permission Matrix

| Người dùng (Actor) | Là Người tạo (`created_by == user.id`) | Là Trainer được gán (`trainer.id == user.id`) | Có Role Admin / Leader | Quyền Đánh giá Tổng thể (`overall`) | Quyền Đánh giá Học viên (`trainer`) | Nút hiển thị trên UI |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Admin / Leader** | Bất kỳ | Bất kỳ | Có | Cho phép | Cho phép | Hiển thị đầy đủ |
| **Người tạo cuộc họp (Non-admin)** | Có | Không/Có | Không | Cho phép | Cho phép | Hiển thị đầy đủ |
| **Trainer được gán (Non-admin)** | Không | Có | Không | Cho phép | Cho phép | Hiển thị đầy đủ |
| **Học viên thường** | Không | Không | Không | Từ chối (403) | Từ chối (403) | Ẩn hoàn toàn |
