"""Value Objects for Chatbot Domain."""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCallRecord(BaseModel):
    """Record of a tool call invoked by the assistant."""

    tool_name: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    execution_status: str = "success"  # "success" | "error" | "duplicate_skipped"
    iteration_index: int = 1


@dataclass
class AgentLoopState:
    """Tracks state and guards for autonomous multi-turn tool loops."""

    iteration: int = 0
    max_iterations: int = 5
    accumulated_content: str = ""
    accumulated_reasoning: str = ""
    executed_tools: list[ToolCallRecord] = field(default_factory=list)
    call_signatures: set[str] = field(default_factory=set)
    is_completed: bool = False

    def add_call_signature(self, tool_name: str, args: dict[str, Any]) -> bool:
        """Returns True if call is new, False if identical call was executed before."""
        try:
            serialized_args = json.dumps(args, sort_keys=True, ensure_ascii=False)
        except Exception:
            serialized_args = str(args)
        signature = f"{tool_name}:{serialized_args}"
        if signature in self.call_signatures:
            return False
        self.call_signatures.add(signature)
        return True


class ChatMessageMetadata(BaseModel):
    """Strongly-typed metadata for chat messages (Constitution XVII)."""

    model_name: str = "ggml-org/gemma-4-e4b-it-GGUF:Q4_0"
    reasoning_content: str | None = None
    tools_invoked: list[ToolCallRecord] = Field(default_factory=list)
    citations: list[str] = Field(default_factory=list)
    usage: dict[str, Any] | None = None
    timings: dict[str, Any] | None = None


class AgentStreamEvent(BaseModel):
    """Domain event emitted during Agent reasoning and tool loop execution."""

    event_type: str
    data: Any
