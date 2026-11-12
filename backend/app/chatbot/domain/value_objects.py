"""Value Objects for Chatbot Domain."""

from enum import StrEnum

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCallRecord(BaseModel):
    """Record of a tool call invoked by the assistant."""

    tool_name: str
    arguments: dict[str, str | int | float | bool] = Field(default_factory=dict)
    execution_status: str = "success"


class ChatMessageMetadata(BaseModel):
    """Strongly-typed metadata for chat messages (Constitution XVII)."""

    model_name: str = "ggml-org/gemma-4-e4b-it-GGUF:Q4_0"
    reasoning_content: str | None = None
    tools_invoked: list[ToolCallRecord] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
