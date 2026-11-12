"""Chat Repository — Data Access Layer for Chatbot.

Implements FIFO pruning rule (max 5 sessions per user) and cascade message management.
Uses flush() instead of commit() following project Clean Architecture.
"""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.chatbot.domain.entity import ChatMessage, ChatSession
from app.chatbot.infrastructure.models import ChatMessageModel, ChatSessionModel


class ChatRepository:
    """Repository handling persistence for ChatSession and ChatMessage."""

    MAX_SESSIONS_PER_USER = 5

    def __init__(self, session: Session) -> None:
        self.session = session

    def get_user_sessions(self, user_id: int) -> list[ChatSession]:
        """Get all active chat sessions of a user ordered by updated_at descending (max 5)."""
        stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.user_id == user_id)
            .order_by(ChatSessionModel.updated_at.desc())
            .limit(self.MAX_SESSIONS_PER_USER)
        )
        models = self.session.scalars(stmt).all()
        return [m.to_entity(include_messages=False) for m in models]

    def get_session_by_id(
        self, session_id: UUID, user_id: int, include_messages: bool = False
    ) -> ChatSession | None:
        """Get a specific session owned by user_id."""
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
        )
        if include_messages:
            stmt = stmt.options(selectinload(ChatSessionModel.messages))

        model = self.session.scalars(stmt).first()
        return model.to_entity(include_messages=include_messages) if model else None

    def create_session(self, session: ChatSession) -> ChatSession:
        """Create a new session, enforcing the max 5 sessions FIFO pruning rule."""
        # 1. Enforce FIFO pruning if user already has >= MAX_SESSIONS_PER_USER
        existing_stmt = (
            select(ChatSessionModel)
            .where(ChatSessionModel.user_id == session.user_id)
            .order_by(ChatSessionModel.updated_at.asc())
        )
        existing_sessions = list(self.session.scalars(existing_stmt).all())

        # If 5 or more exist, delete the oldest to make room for the new one
        if len(existing_sessions) >= self.MAX_SESSIONS_PER_USER:
            excess_count = len(existing_sessions) - self.MAX_SESSIONS_PER_USER + 1
            for old_model in existing_sessions[:excess_count]:
                self.session.delete(old_model)
            self.session.flush()

        # 2. Insert new session
        model = ChatSessionModel.from_entity(session)
        self.session.add(model)
        self.session.flush()
        return model.to_entity(include_messages=False)

    def update_session(self, session: ChatSession) -> ChatSession:
        """Update an existing session's title and updated_at timestamp."""
        model = self.session.get(ChatSessionModel, session.id)
        if model and model.user_id == session.user_id:
            model.title = session.title
            model.updated_at = datetime.now(UTC)
            self.session.flush()
            return model.to_entity(include_messages=False)
        return session

    def delete_session(self, session_id: UUID, user_id: int) -> bool:
        """Delete a chat session and cascade delete all its messages."""
        stmt = select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
        )
        model = self.session.scalars(stmt).first()
        if model:
            self.session.delete(model)
            self.session.flush()
            return True
        return False

    def add_message(self, message: ChatMessage) -> ChatMessage:
        """Add a new chat message to a session and touch session updated_at."""
        model = ChatMessageModel.from_entity(message)
        self.session.add(model)

        # Touch parent session's updated_at
        session_model = self.session.get(ChatSessionModel, message.session_id)
        if session_model:
            session_model.updated_at = datetime.now(UTC)

        self.session.flush()
        return model.to_entity()

    def get_session_messages(
        self, session_id: UUID, user_id: int
    ) -> list[ChatMessage]:
        """Get all messages of a session owned by user_id in chronological order."""
        # Verify ownership first
        owner_stmt = select(ChatSessionModel.id).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == user_id,
        )
        if not self.session.scalars(owner_stmt).first():
            return []

        stmt = (
            select(ChatMessageModel)
            .where(ChatMessageModel.session_id == session_id)
            .order_by(ChatMessageModel.created_at.asc())
        )
        models = self.session.scalars(stmt).all()
        return [m.to_entity() for m in models]
