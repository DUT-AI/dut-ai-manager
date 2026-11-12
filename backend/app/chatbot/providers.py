"""Dishka Dependency Injection Provider for Chatbot Domain."""

from dishka import Provider, Scope, provide
from sqlalchemy.orm import Session

from app.chatbot.application import (
    DeleteChatSessionUseCase,
    GetChatSessionsUseCase,
    GetQuickPromptsUseCase,
    GetSessionMessagesUseCase,
    SendChatMessageUseCase,
)
from app.chatbot.infrastructure.llm_client import LLMClient
from app.chatbot.infrastructure.repository import ChatRepository
from app.chatbot.infrastructure.tools_registry import ChatbotToolRegistry


class ChatbotModuleProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def get_chat_repo(self, session: Session) -> ChatRepository:
        return ChatRepository(session)

    @provide
    def get_llm_client(self) -> LLMClient:
        return LLMClient()

    @provide
    def get_tool_registry(self, session: Session) -> ChatbotToolRegistry:
        return ChatbotToolRegistry(session)

    @provide
    def get_send_chat_message_uc(
        self,
        repo: ChatRepository,
        llm_client: LLMClient,
        tool_registry: ChatbotToolRegistry,
    ) -> SendChatMessageUseCase:
        return SendChatMessageUseCase(repo, llm_client, tool_registry)

    @provide
    def get_chat_sessions_uc(self, repo: ChatRepository) -> GetChatSessionsUseCase:
        return GetChatSessionsUseCase(repo)

    @provide
    def get_session_messages_uc(
        self, repo: ChatRepository
    ) -> GetSessionMessagesUseCase:
        return GetSessionMessagesUseCase(repo)

    @provide
    def get_delete_chat_session_uc(
        self, repo: ChatRepository
    ) -> DeleteChatSessionUseCase:
        return DeleteChatSessionUseCase(repo)

    @provide
    def get_quick_prompts_uc(self) -> GetQuickPromptsUseCase:
        return GetQuickPromptsUseCase()
