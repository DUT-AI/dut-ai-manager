# Data Model: Chatbot UUID Primary Keys

## ER Diagram (PostgreSQL)

```
┌────────────────────────────────────────────────────────┐
│                     chat_sessions                      │
├────────────────────────────────────────────────────────┤
│ id: UUID (PK, UUIDv7 default)                          │
│ user_id: INTEGER (FK -> users.id, ON DELETE CASCADE)   │
│ title: VARCHAR(255)                                    │
│ created_at: TIMESTAMPTZ                                │
│ updated_at: TIMESTAMPTZ                                │
└──────────────────────────┬─────────────────────────────┘
                           │ 1
                           │
                           │ N (ON DELETE CASCADE)
┌──────────────────────────▼─────────────────────────────┐
│                     chat_messages                      │
├────────────────────────────────────────────────────────┤
│ id: UUID (PK, UUIDv7 default)                          │
│ session_id: UUID (FK -> chat_sessions.id)              │
│ role: VARCHAR(32)                                      │
│ content: TEXT                                          │
│ metadata_json: JSONB                                   │
│ created_at: TIMESTAMPTZ                                │
│ updated_at: TIMESTAMPTZ                                │
└────────────────────────────────────────────────────────┘
```

## Indexes
- `chat_sessions`:
  - `ix_chat_sessions_user_id` on `user_id`
  - `ix_chat_sessions_created_at` on `created_at`
- `chat_messages`:
  - `ix_chat_messages_session_id` on `session_id`
  - `ix_chat_messages_created_at` on `created_at`
