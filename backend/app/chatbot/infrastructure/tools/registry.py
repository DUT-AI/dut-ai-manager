"""Chatbot Tool Registry implementing the Open-Closed Principle (OCP).

Allows new tools to be added seamlessly without modifying existing execution or filtering logic.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.chatbot.infrastructure.tools import (
    BaseChatbotTool,
    DbExecuteQueryTool,
    DbGetTableRelationshipsTool,
    DbGetTableSchemaTool,
    DbListTablesTool,
    GetMyViolationsTool,
    GetViolationPoliciesTool,
)
from app.core.principal import AuthPrincipal


class ChatbotToolRegistry:
    """Registry providing tool discovery and execution for the LLM.

    Adheres to the Open-Closed Principle:
    - New tools can be registered dynamically via `register()`.
    - `get_tool_definitions()` and `execute_tool()` delegate directly to each tool instance
      without hardcoded `if/elif` statements.
    """

    def __init__(self, session: Session, tools: list[BaseChatbotTool] | None = None) -> None:
        self.session = session
        self._tools: dict[str, BaseChatbotTool] = {}

        if tools is None:
            self._register_default_tools()
        else:
            for tool in tools:
                self.register(tool)

    def _register_default_tools(self) -> None:
        """Register the built-in system tools."""
        default_tools: list[BaseChatbotTool] = [
            GetMyViolationsTool(),
            GetViolationPoliciesTool(),
            DbListTablesTool(),
            DbGetTableSchemaTool(),
            DbGetTableRelationshipsTool(),
            DbExecuteQueryTool(),
        ]
        for tool in default_tools:
            self.register(tool)

    def register(self, tool: BaseChatbotTool) -> "ChatbotToolRegistry":
        """Register a new tool instance in the registry."""
        self._tools[tool.name] = tool
        return self

    def unregister(self, tool_name: str) -> None:
        """Remove a tool from the registry."""
        self._tools.pop(tool_name, None)

    def get_tool(self, tool_name: str) -> BaseChatbotTool | None:
        """Retrieve a registered tool by its name."""
        return self._tools.get(tool_name)

    def get_tool_definitions(self, user: AuthPrincipal) -> list[dict[str, Any]]:
        """Return OpenAI-compatible tool specifications filtered by the user's permissions."""
        return [
            tool.to_openai_schema()
            for tool in self._tools.values()
            if tool.is_allowed(user)
        ]

    def execute_tool(
        self, tool_name: str, args: dict[str, Any], user: AuthPrincipal
    ) -> dict[str, Any]:
        """Safely execute the requested tool with RBAC check and IDOR protection.

        Zero `if/elif` branches: delegates directly to the matched `BaseChatbotTool`.
        """
        tool = self._tools.get(tool_name)
        if not tool:
            return {"error": f"Không tìm thấy công cụ '{tool_name}'."}

        if not tool.is_allowed(user):
            return {"error": "Bạn không có quyền truy cập dữ liệu từ công cụ này."}

        try:
            with self.session.begin_nested():
                return tool.execute(self.session, args, user)
        except Exception as ex:
            return {
                "error": f"Lỗi trong quá trình thực thi công cụ '{tool_name}': {str(ex)}"
            }
