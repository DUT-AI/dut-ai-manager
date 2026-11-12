"""Use Case to delete a chat session and its associated messages."""

from app.chatbot.infrastructure.repository import ChatRepository


class DeleteChatSessionUseCase:
    """Deletes a chat session belonging to the user."""

    def __init__(self, repo: ChatRepository) -> None:
        self.repo = repo

    def execute(self, session_id: int, user_id: int) -> bool:
        return self.repo.delete_session(session_id, user_id)
