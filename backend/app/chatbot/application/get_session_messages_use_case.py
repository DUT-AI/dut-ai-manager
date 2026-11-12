"""Use Case to retrieve chronological messages of a specific chat session."""

from uuid import UUID

from app.chatbot.domain.entity import ChatMessage
from app.chatbot.infrastructure.repository import ChatRepository


class GetSessionMessagesUseCase:
    """Retrieves messages for a session, verifying user ownership."""

    def __init__(self, repo: ChatRepository) -> None:
        self.repo = repo

    def execute(self, session_id: UUID, user_id: int) -> list[ChatMessage]:
        return self.repo.get_session_messages(session_id, user_id)
