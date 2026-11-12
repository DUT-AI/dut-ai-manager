"""LLM Client Adapter for OpenAI-compatible Endpoint (https://llm2.dutai.site/v1).

Streams SSE chunks asynchronously using aiohttp and accumulates streaming tool calls.
"""

import json
from collections.abc import AsyncGenerator
from typing import Any

import aiohttp
from loguru import logger

from app.core.config import settings


class LLMClient:
    """Async client communicating with the on-premise OpenAI-compatible LLM server."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY

    @staticmethod
    def _accumulate_tool_delta(
        tool_delta: list[dict[str, Any]],
        accumulated: dict[int, dict[str, Any]],
    ) -> None:
        """Merge incremental tool_call chunks into complete tool_call objects."""
        for part in tool_delta:
            idx = part.get("index", 0)
            if idx not in accumulated:
                accumulated[idx] = {
                    "id": part.get("id", f"call_{idx}"),
                    "type": "function",
                    "function": {"name": "", "arguments": ""},
                }

            if call_id := part.get("id"):
                accumulated[idx]["id"] = call_id
            if call_type := part.get("type"):
                accumulated[idx]["type"] = call_type

            func_delta = part.get("function", {})
            if name_chunk := func_delta.get("name"):
                accumulated[idx]["function"]["name"] += name_chunk
            if arg_chunk := func_delta.get("arguments"):
                accumulated[idx]["function"]["arguments"] += arg_chunk

    async def stream_chat(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int = 1500,
        temperature: float = 0.3,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Stream chat completions from the LLM endpoint yielding SSE deltas."""
        url = f"{self.base_url}/chat/completions"
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": True,
        }
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        timeout = aiohttp.ClientTimeout(total=60, connect=10)
        accumulated_tools: dict[int, dict[str, Any]] = {}

        try:
            async with (
                aiohttp.ClientSession(timeout=timeout) as session,
                session.post(url, json=payload, headers=headers) as response,
            ):
                if response.status != 200:
                    err_text = await response.text()
                    logger.error(f"LLM API returned HTTP {response.status}: {err_text}")
                    yield {"type": "error", "data": f"Lỗi máy chủ LLM (HTTP {response.status})"}
                    return

                async for line_bytes in response.content:
                    line = line_bytes.decode("utf-8").strip()
                    if not line or not line.startswith("data: "):
                        continue
                    data_str = line[6:].strip()
                    if data_str == "[DONE]":
                        break

                    try:
                        chunk = json.loads(data_str)
                        choices = chunk.get("choices", [])
                        if not choices:
                            continue
                        delta = choices[0].get("delta", {})

                        if reasoning := delta.get("reasoning_content"):
                            yield {"type": "reasoning", "data": reasoning}
                        elif content := delta.get("content"):
                            yield {"type": "content", "data": content}
                        elif tool_calls_delta := delta.get("tool_calls"):
                            self._accumulate_tool_delta(tool_calls_delta, accumulated_tools)
                    except json.JSONDecodeError:
                        continue

            if accumulated_tools:
                complete_tools = list(accumulated_tools.values())
                yield {"type": "tool_calls_complete", "data": complete_tools}

            yield {"type": "done", "data": ""}

        except Exception as e:
            logger.error(f"Failed to communicate with LLM server: {e}")
            yield {"type": "error", "data": f"Không thể kết nối đến máy chủ AI: {str(e)}"}
