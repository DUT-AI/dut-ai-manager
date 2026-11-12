"""Use Case to retrieve a user's active chat sessions (max 5)."""

from app.chatbot.domain.entity import ChatSession
from app.chatbot.infrastructure.repository import ChatRepository


class GetChatSessionsUseCase:
    """Retrieves up to 5 most recent chat sessions for the authenticated user."""

    def __init__(self, repo: ChatRepository) -> None:
        self.repo = repo

    def execute(self, user_id: int) -> list[ChatSession]:
        return self.repo.get_user_sessions(user_id)
