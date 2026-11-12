# Research: Chatbot UUID Primary Keys Migration

## 1. Cơ chế UUIDv7 trong DUT AI Manager
Dự án đã định nghĩa sẵn mixin và generator:
- Generator: `from app.shared.domain.uuid_utils import uuid7`
- Mixin: `from app.shared.infrastructure.base_model import SQLAlchemyUuidPrimaryKeyMixin`
- Kiểu cột SQLAlchemy: `from sqlalchemy import UUID as SQLAlchemyUUID`
  ```python
  id: Mapped[UUID] = mapped_column(
      SQLAlchemyUUID(as_uuid=True),
      primary_key=True,
      default=uuid7,
  )
  ```

## 2. Chiến lược Migration (Alembic)
Vì người dùng chấp thuận xóa toàn bộ dữ liệu lịch sử chat hiện tại:
- Thực hiện `op.drop_table('chat_messages')` và `op.drop_table('chat_sessions')`.
- Thực hiện tạo lại `chat_sessions` với `id` là `sa.UUID(as_uuid=True)`.
- Thực hiện tạo lại `chat_messages` với `id` là `sa.UUID(as_uuid=True)` và `session_id` là `sa.UUID(as_uuid=True)` kèm khóa ngoại `ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE')`.

## 3. Ảnh hưởng đến Use Cases và API Contracts
- `POST /api/v1/chatbot/chat`: Nhận `session_id: UUID | None = None`. Trả về SSE event `session_created` chứa `id: str` (UUID).
- `GET /api/v1/chatbot/sessions`: Trả về danh sách sessions với `id: UUID`.
- `GET /api/v1/chatbot/sessions/{session_id}/messages`: Path param `session_id: UUID`.
- `DELETE /api/v1/chatbot/sessions/{session_id}`: Path param `session_id: UUID`.

## 4. Frontend Impact
- Toàn bộ các interface `sessionId` và `id` được chuyển từ `number` sang `string`.
- Các mock ID trong optimistic updates đổi từ `Date.now()` (number) sang `crypto.randomUUID()` (string chuẩn UUID).
