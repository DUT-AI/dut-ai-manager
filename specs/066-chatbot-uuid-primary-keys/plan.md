# Implementation Plan: Chatbot UUID Primary Keys Migration

**Branch**: `066-chatbot-uuid-primary-keys` | **Date**: 2026-11-12 | **Spec**: [spec.md](./spec.md)

**Input**: User request: "Tôi muốn chỉnh sửa lại id của các bảng liên quan đế chatbot là SQLAlchemyUuidPrimaryKeyMixin thay vì int như hiện tại => Chấp nhận xóa toàn bộ bảng ghi hiện tại"

## Summary
Chuyển đổi toàn diện khóa chính và khóa ngoại của các bảng Chatbot (`chat_sessions`, `chat_messages`) từ kiểu số nguyên tự tăng (`SQLAlchemyIntPrimaryKeyMixin`) sang chuẩn `SQLAlchemyUuidPrimaryKeyMixin` (RFC 9562 UUIDv7). Tạo file migration Alembic tái tạo bảng sạch sẽ, cập nhật Domain Entity, DTOs, Use Cases, Controller và Frontend TypeScript types từ `number` sang `string` (UUID).

## Technical Context

**Language/Version**: Python 3.12 (Backend FastAPI), TypeScript 5.x (Frontend React/Vite)  
**Primary Dependencies**: SQLAlchemy 2.0, Dishka DI, Pydantic V2, Alembic, React, Axios, TanStack Query  
**Storage**: PostgreSQL (`UUID` column type)  
**Testing**: pytest (Backend), tsc typecheck & vite build (Frontend)  
**Target Platform**: Web application  
**Project Type**: Full-stack web application (Backend REST API + Frontend SPA)  
**Performance Goals**: N/A (UUIDv7 preserves time-ordered indexing efficiency in B-Tree)  
**Constraints**: Truncate/Drop sạch các bản ghi chat hiện tại (đã được chấp thuận)  
**Scale/Scope**: 2 bảng database (`chat_sessions`, `chat_messages`), 6 files backend, 5 files frontend, unit tests  

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- [x] **Zero Regressions**: Chuyển đổi ID không ảnh hưởng đến các bảng ngoài chatbot (`users`, `violations` v.v.).
- [x] **Clean Architecture**: Domain Entities dùng `BaseGenericEntity[UUID]`, không import SQLAlchemy vào Domain.
- [x] **Safe Database Change**: Người dùng đã chấp thuận xóa dữ liệu cũ, migration sẽ drop bảng cũ và tạo bảng mới với kiểu cột `UUID`.
- [x] **Type Safety**: Cập nhật cả Backend Pydantic DTOs và Frontend TypeScript types đồng bộ.

## Project Structure

### Documentation (this feature)

```text
specs/066-chatbot-uuid-primary-keys/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
└── quickstart.md
```

## Phase 0: Research & Key Decisions
- Xem xét `SQLAlchemyUuidPrimaryKeyMixin`: Đã có sẵn trong `app.shared.infrastructure.base_model.py`. Khóa chính tự động sinh bằng hàm `uuid7`.
- `chat_messages.session_id` là khóa ngoại trỏ tới `chat_sessions.id`: Cần đổi cột `session_id` thành `Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)`.
- `chat_messages.id` và `chat_sessions.id`: Đều là UUID.
- Frontend: Cần đổi kiểu `id` và `sessionId` từ `number` sang `string`.

## Phase 1: Data Model & Contracts
- **Bảng `chat_sessions`**:
  - `id`: `UUID` (Primary Key, RFC 9562 UUIDv7)
  - `user_id`: `Integer` (Foreign Key -> `users.id`)
  - `title`: `VARCHAR(255)`
  - `created_at`: `TIMESTAMPTZ`
  - `updated_at`: `TIMESTAMPTZ`
- **Bảng `chat_messages`**:
  - `id`: `UUID` (Primary Key, RFC 9562 UUIDv7)
  - `session_id`: `UUID` (Foreign Key -> `chat_sessions.id`)
  - `role`: `VARCHAR(32)`
  - `content`: `TEXT`
  - `metadata_json`: `JSONB`
  - `created_at`: `TIMESTAMPTZ`
  - `updated_at`: `TIMESTAMPTZ`

## Phase 2: Implementation Steps
1. **Backend Migration & Models**:
   - Chỉnh sửa `backend/app/chatbot/infrastructure/models.py`: Kế thừa `SQLAlchemyUuidPrimaryKeyMixin`, đổi kiểu `session_id` sang `UUID`.
   - Chỉnh sửa `backend/app/chatbot/domain/entity.py`: Kế thừa `BaseGenericEntity[UUID]`, đổi `session_id: UUID`.
   - Chỉnh sửa `backend/app/chatbot/schemas.py`: Đổi `id` và `session_id` thành `UUID`.
   - Tạo Alembic migration script chuyển đổi bảng (`op.drop_table` rồi `op.create_table` với kiểu `sa.UUID(as_uuid=True)`).
   - Chạy `poetry run alembic upgrade head`.
2. **Backend Application & Infrastructure**:
   - Chỉnh sửa `repository.py`, `controller.py`, `send_chat_message_use_case.py`, `get_session_messages_use_case.py`, `delete_chat_session_use_case.py` nhận `UUID` (hoặc `UUID | str`).
3. **Frontend Types & Services**:
   - Cập nhật `frontend/src/features/chatbot/types/chatbot.types.ts`: Cập nhật kiểu `id` và `sessionId` thành `string`.
   - Cập nhật `chatbot.service.ts`: `sessionId: string`.
   - Cập nhật `useChatbot.ts`, `useChatSessions.ts`, `ChatWindow.tsx`, `ChatbotPage.tsx`, `ChatSessionSidebar.tsx`, `FloatingChatButton.tsx`.
4. **Testing & Verification**:
   - Cập nhật unit tests `backend/tests/unit/test_chatbot.py`.
   - Chạy `poetry run pytest`.
   - Chạy `npm run build` ở frontend.
