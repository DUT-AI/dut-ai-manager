"""Domain Entities for Chatbot."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import Field

from app.chatbot.domain.value_objects import ChatMessageMetadata, MessageRole
from app.shared.domain.base_entity import BaseUuidEntity


class ChatMessage(BaseUuidEntity):
    """Domain entity representing a message in a chat session."""

    session_id: UUID
    role: MessageRole
    content: str
    metadata_info: ChatMessageMetadata = Field(default_factory=ChatMessageMetadata)


class ChatSession(BaseUuidEntity):
    """Domain entity representing a user's chat session (max 5 sessions per user)."""

    user_id: int
    title: str = "Cuộc trò chuyện mới"
    messages: list[ChatMessage] = Field(default_factory=list)

    def update_title_from_first_message(self, first_user_message: str) -> None:
        """Automatically create a concise title from the user's first query."""
        clean = first_user_message.strip()
        self.title = clean[:50] + ("..." if len(clean) > 50 else "")
        self.updated_at = datetime.now(UTC)
