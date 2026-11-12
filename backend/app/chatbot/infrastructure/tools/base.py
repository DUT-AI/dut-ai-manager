"""Base Abstract Class for Chatbot Tools (Open-Closed Principle).

Every tool encapsulates its own name, description, JSON parameters schema,
permission requirement, and execution logic.
"""

from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy.orm import Session

from app.core.principal import AuthPrincipal


class BaseChatbotTool(ABC):
    """Abstract base class representing an executable LLM tool."""

    name: str
    description: str
    parameters: dict[str, Any]
    required_permissions: list[str] = []

    def is_allowed(self, user: AuthPrincipal) -> bool:
        """Check if the user is authorized to view and execute this tool.

        - If required_permissions is empty, any authenticated user can access.
        - If required_permissions has permissions, user must possess at least one,
          or have admin role.
        """
        if not self.required_permissions:
            return True

        if any(r.lower() == "admin" for r in user.role_names):
            return True

        user_perms = user.permissions or set()
        return any(perm in user_perms for perm in self.required_permissions)

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert tool specification to standard OpenAI/LLM Function Calling format."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    @abstractmethod
    def execute(
        self, session: Session, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        """Execute the tool against the database session with strict IDOR protection."""
        pass
