"""Pydantic Request and Response Schemas for Chatbot API."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.chatbot.domain.value_objects import ChatMessageMetadata, MessageRole


class SendChatRequest(BaseModel):
    """Payload to send a message to the chatbot."""

    message: str = Field(..., min_length=1, max_length=4000, description="Nội dung câu hỏi của người dùng")
    session_id: UUID | None = Field(default=None, description="ID phiên trò chuyện (nếu có)")


class ChatSessionDto(BaseModel):
    """Response DTO representing a chat session."""

    id: UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageDto(BaseModel):
    """Response DTO representing an individual chat message."""

    id: UUID
    session_id: UUID
    role: MessageRole
    content: str
    metadata_info: ChatMessageMetadata
    created_at: datetime


class QuickPromptItem(BaseModel):
    """Response DTO for role-adaptive quick question suggestions."""

    label: str
    prompt: str
    category: str = Field(..., description="'personal' hoặc 'administrative'")
