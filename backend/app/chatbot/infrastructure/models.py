"""SQLAlchemy ORM Models for Chatbot."""

from datetime import UTC, datetime
from typing import Any

from pydantic import TypeAdapter
from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, TypeDecorator

from app.chatbot.domain.entity import ChatMessage, ChatSession
from app.chatbot.domain.value_objects import ChatMessageMetadata, MessageRole
from app.shared.infrastructure.base_model import (
    Base,
    SQLAlchemyIntPrimaryKeyMixin,
    SQLAlchemyTimestampOnlyMixin,
)


class ChatMessageMetadataJSON(TypeDecorator[ChatMessageMetadata]):
    """SQLAlchemy TypeDecorator for strongly-typed ChatMessageMetadata (Constitution XVII)."""

    impl = JSON
    cache_ok = True
    _adapter = TypeAdapter(ChatMessageMetadata)

    def process_bind_param(
        self, value: object, dialect: object
    ) -> dict[str, Any] | None:
        if value is None:
            return None
        if isinstance(value, ChatMessageMetadata):
            return value.model_dump(mode="json")
        if isinstance(value, dict):
            parsed = self._adapter.validate_python(value)
            return self._adapter.dump_python(parsed, mode="json")
        return None

    def process_result_value(
        self, value: object, dialect: object
    ) -> ChatMessageMetadata:
        if value is None:
            return ChatMessageMetadata()
        if isinstance(value, ChatMessageMetadata):
            return value
        if isinstance(value, dict):
            return self._adapter.validate_python(value)
        return ChatMessageMetadata()


class ChatSessionModel(
    SQLAlchemyIntPrimaryKeyMixin, SQLAlchemyTimestampOnlyMixin, Base
):
    __tablename__ = "chat_sessions"

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(255), default="Cuộc trò chuyện mới", nullable=False
    )

    # Relationships
    messages: Mapped[list["ChatMessageModel"]] = relationship(
        "ChatMessageModel",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessageModel.created_at.asc()",
    )

    def to_entity(self, include_messages: bool = False) -> ChatSession:
        return ChatSession(
            id=self.id,
            user_id=self.user_id,
            title=self.title,
            created_at=self.created_at or datetime.now(UTC),
            updated_at=self.updated_at or datetime.now(UTC),
            messages=[m.to_entity() for m in self.messages] if include_messages else [],
        )

    @classmethod
    def from_entity(cls, entity: ChatSession) -> "ChatSessionModel":
        model = cls(
            user_id=entity.user_id,
            title=entity.title,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        if entity.id is not None:
            model.id = entity.id
        return model


class ChatMessageModel(
    SQLAlchemyIntPrimaryKeyMixin, SQLAlchemyTimestampOnlyMixin, Base
):
    __tablename__ = "chat_messages"

    session_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(32), nullable=False
    )  # "user" | "assistant" | "system"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[ChatMessageMetadata] = mapped_column(
        ChatMessageMetadataJSON, default=ChatMessageMetadata, nullable=False
    )

    # Relationships
    session: Mapped["ChatSessionModel"] = relationship(
        "ChatSessionModel", back_populates="messages"
    )

    def to_entity(self) -> ChatMessage:
        return ChatMessage(
            id=self.id,
            session_id=self.session_id,
            role=MessageRole(self.role),
            content=self.content,
            metadata_info=self.metadata_json,
            created_at=self.created_at or datetime.now(UTC),
            updated_at=self.updated_at or datetime.now(UTC),
        )

    @classmethod
    def from_entity(cls, entity: ChatMessage) -> "ChatMessageModel":
        model = cls(
            session_id=entity.session_id,
            role=entity.role.value,
            content=entity.content,
            metadata_json=entity.metadata_info,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
        if entity.id is not None:
            model.id = entity.id
        return model
