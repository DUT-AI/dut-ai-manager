"""Use Case to orchestrate session management, message persistence, and SSE streaming."""

import json
from collections.abc import AsyncGenerator
from typing import Any
from uuid import UUID

from app.chatbot.domain.agent import Agent
from app.chatbot.domain.entity import ChatMessage, ChatSession
from app.chatbot.domain.value_objects import (
    ChatMessageMetadata,
    MessageRole,
)
from app.chatbot.infrastructure.repository import ChatRepository
from app.core.principal import AuthPrincipal


class SendChatMessageUseCase:
    """Orchestrates chat session lifecycle, persistence, and SSE event streaming via Agent Domain Service."""

    def __init__(self, repo: ChatRepository, agent: Agent) -> None:
        self.repo = repo
        self.agent = agent

    def _resolve_session(
        self, session_id: UUID | None, user_id: int, message: str
    ) -> tuple[ChatSession, bool]:
        if session_id:
            if existing := self.repo.get_session_by_id(session_id, user_id):
                return existing, False

        new_session = ChatSession(user_id=user_id)
        new_session.update_title_from_first_message(message)
        return self.repo.create_session(new_session), True

    async def execute(
        self,
        message: str,
        session_id: UUID | None,
        user: AuthPrincipal,
    ) -> AsyncGenerator[str, None]:
        """Process chat message and yield SSE formatted chunks via the Agent Domain Service."""
        session, is_new = self._resolve_session(session_id, user.user_id, message)
        if is_new:
            payload = {"type": "session_created", "data": {"id": str(session.id), "title": session.title}}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        self.repo.add_message(ChatMessage(session_id=session.id, role=MessageRole.USER, content=message))
        history = self.repo.get_session_messages(session.id, user.user_id)

        completion_data: dict[str, Any] | None = None

        async for event in self.agent.run_stream(history[-8:], user):
            if event.event_type == "complete":
                completion_data = event.data
            elif event.event_type == "usage":
                continue
            else:
                payload = {"type": event.event_type, "data": event.data}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        if completion_data:
            content = completion_data.get("content", "")
            metadata = completion_data.get("metadata")
            self.repo.add_message(
                ChatMessage(
                    session_id=session.id,
                    role=MessageRole.ASSISTANT,
                    content=content,
                    metadata_info=metadata if isinstance(metadata, ChatMessageMetadata) else ChatMessageMetadata(),
                )
            )
            yield f"data: {json.dumps({'type': 'done', 'data': content}, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"
