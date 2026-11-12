"""Backward-compatibility module and exports for Chatbot Tools.

Redirects imports to the modular `app.chatbot.infrastructure.tools` package.
"""

from app.chatbot.infrastructure.tools.base import BaseChatbotTool
from app.chatbot.infrastructure.tools.registry import ChatbotToolRegistry

__all__ = ["ChatbotToolRegistry", "BaseChatbotTool"]
