---
description: "Task list for Chatbot UUID Primary Keys Migration"
---

# Tasks: Chatbot UUID Primary Keys Migration

**Input**: Design documents from `/specs/066-chatbot-uuid-primary-keys/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

## Organization:
Tasks are grouped into 4 execution phases:
1. **Phase 1: Database & ORM Migration** (Foundation)
2. **Phase 2: Backend Clean Architecture Updates** (Domain, DTOs, Repository, Use Cases, Controller)
3. **Phase 3: Frontend Type & Service Alignment** (TypeScript Types, Services, Hooks, Components)
4. **Phase 4: Testing & Verification** (Unit Tests, Frontend Build)

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel
- Exact file paths included for every task

---

## Phase 1: Database & ORM Migration (Foundation)

**Purpose**: Update ORM models to `SQLAlchemyUuidPrimaryKeyMixin` and create an Alembic migration script to drop old integer-based tables and recreate tables using PostgreSQL `UUID`.

- [x] T001 Update `ChatSessionModel` and `ChatMessageModel` in `backend/app/chatbot/infrastructure/models.py` to inherit `SQLAlchemyUuidPrimaryKeyMixin` and change `session_id` to `Mapped[UUID] = mapped_column(SQLAlchemyUUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), index=True, nullable=False)`.
- [x] T002 Create Alembic migration script in `backend/alembic/versions/b0a90fa04270_migrate_chat_tables_to_uuid.py` dropping existing `chat_messages` and `chat_sessions` tables and recreating them with UUID primary keys and foreign keys.
- [x] T003 Execute `poetry run alembic upgrade head` to apply database schema changes.

**Checkpoint**: Database schema updated to UUID primary and foreign keys.

---

## Phase 2: Backend Clean Architecture Updates

**Purpose**: Update Domain Entities, Pydantic DTOs, Repository, Use Cases, and Controller to use `UUID` instead of `int`.

- [x] T004 [P] Update domain entities in `backend/app/chatbot/domain/entity.py`: `ChatMessage(BaseGenericEntity[UUID])` with `session_id: UUID` and `ChatSession(BaseGenericEntity[UUID])`.
- [x] T005 [P] Update DTO schemas in `backend/app/chatbot/schemas.py`: Change `session_id: UUID | None` in `SendChatRequest`, `session_id: UUID` and `id: UUID` in `ChatMessageDto` & `ChatSessionDto`.
- [x] T006 Update `ChatRepository` in `backend/app/chatbot/infrastructure/repository.py`: Adjust methods `get_user_sessions`, `get_session_by_id`, `delete_session`, and `get_session_messages` to accept and query with `session_id: UUID`.
- [x] T007 Update Use Cases in `backend/app/chatbot/application/`:
  - `send_chat_message_use_case.py`: Accept `session_id: UUID | None` and handle UUID in session resolution.
  - `get_session_messages_use_case.py`: Accept `session_id: UUID`.
  - `delete_chat_session_use_case.py`: Accept `session_id: UUID`.
- [x] T008 Update API Controller endpoints in `backend/app/chatbot/controller.py`: Update route path parameters `/sessions/{session_id}` to `session_id: UUID`.

**Checkpoint**: Backend API compiles and runs with UUIDs across all chatbot endpoints.

---

## Phase 3: Frontend Type & Service Alignment

**Purpose**: Update Frontend types, chatbot services, and React state to use UUID strings (`string | null`).

- [x] T009 Update chatbot TypeScript definitions in `frontend/src/features/chatbot/types/chatbot.types.ts` & regenerate via `npm run generate:api`: Ensure `ChatMessage`, `ChatSession`, and related DTOs type `id` and `session_id` as `string`.
- [x] T010 [P] Update `frontend/src/features/chatbot/services/chatbot.service.ts`: Update parameters and endpoints for `getSessionMessages(sessionId: string)` and `deleteSession(sessionId: string)`.
- [x] T011 [P] Update `frontend/src/features/chatbot/hooks/useChatSessions.ts`: Change mutation parameter from `number` to `string`.
- [x] T012 Update `frontend/src/features/chatbot/hooks/useChatbot.ts`:
  - Change `sessionId` state, props, and actions to `string | null`.
  - Use `crypto.randomUUID()` for temporary message IDs instead of `Date.now()`.
- [x] T013 Update `frontend/src/features/chatbot/pages/ChatbotPage.tsx`, `frontend/src/features/chatbot/components/ChatWindow.tsx`, and `frontend/src/features/chatbot/components/ChatSessionSidebar.tsx`:
  - Change `activeSessionId` and `sessionId` props/state from `number | null` to `string | null`.

**Checkpoint**: Frontend compiles cleanly (`tsc -b && vite build`) without type errors.

---

## Phase 4: Testing & Verification

**Purpose**: Update and run all unit tests and verify end-to-end integration.

- [x] T014 Update unit tests in `backend/tests/unit/test_chatbot.py`: Replace integer session IDs with UUID instances (e.g. `uuid7()` or `uuid.uuid4()`).
- [x] T015 Run backend test suite: `poetry run pytest tests/unit/test_chatbot.py tests/unit/test_database_tools.py`.
- [x] T016 Run frontend build check: `npm run build` in `frontend/`.

---

## Dependencies & Execution Order
- Phase 1 (DB & Models) must complete first.
- Phase 2 (Backend Clean Architecture) depends on Phase 1.
- Phase 3 (Frontend Alignment) can proceed after Phase 2 (or in parallel once DTOs are defined).
- Phase 4 (Testing & Verification) verifies the complete migration.
