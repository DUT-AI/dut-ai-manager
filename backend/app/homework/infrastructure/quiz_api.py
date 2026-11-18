from typing import Any

import httpx
from loguru import logger

from app.core.config import settings


class QuizApiClient:
    """Infrastructure client for interacting with the external Quiz API system."""

    def __init__(self):
        self.base_url = settings.QUIZ_API_URL.rstrip("/")
        self.api_key = settings.QUIZ_API_KEY.strip()

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def get_game_sessions_for_sync(
        self, game_slug: str
    ) -> list[dict[str, Any]] | None:
        """
        Calls GET /api/v1/game/{game_slug}/sessions-for-sync
        Returns full list of completed game sessions for sync.
        Returns None if not found (404).
        """
        url = f"{self.base_url}/api/v1/game/{game_slug}/sessions-for-sync"
        try:
            async with httpx.AsyncClient(
                timeout=10.0, headers=self._get_headers()
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif (
                        isinstance(data, dict)
                        and "data" in data
                        and isinstance(data["data"], list)
                    ):
                        return data["data"]
                    logger.warning(f"Unexpected response structure from {url}: {data}")
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(
                        f"Quiz game sessions-for-sync request failed: status={response.status_code}, url={url}"
                    )
        except Exception as exc:
            err_msg = str(exc) or repr(exc)
            logger.error(
                f"Error calling Quiz sessions-for-sync ({url}): {type(exc).__name__} - {err_msg}"
            )

        return []

    async def get_homework_submissions_for_sync(
        self, homework_slug: str
    ) -> list[dict[str, Any]] | None:
        """
        Calls GET /api/v1/homeworks/{homework_slug}/submissions-for-sync
        Returns full list of coding submissions for sync.
        Returns None if not found (404).
        """
        url = f"{self.base_url}/api/v1/homeworks/{homework_slug}/submissions-for-sync"
        try:
            async with httpx.AsyncClient(
                timeout=10.0, headers=self._get_headers()
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    res_json = response.json()
                    if (
                        isinstance(res_json, dict)
                        and "data" in res_json
                        and isinstance(res_json["data"], list)
                    ):
                        return res_json["data"]
                    elif isinstance(res_json, list):
                        return res_json
                    logger.warning(
                        f"Unexpected response structure from {url}: {res_json}"
                    )
                elif response.status_code == 404:
                    return None
                else:
                    logger.warning(
                        f"Quiz homework submissions-for-sync request failed: status={response.status_code}, url={url}"
                    )
        except Exception as exc:
            err_msg = str(exc) or repr(exc)
            logger.error(
                f"Error calling Quiz submissions-for-sync ({url}): {type(exc).__name__} - {err_msg}"
            )

        return []

    async def get_lesson_exercises(
        self, lesson_slug: str
    ) -> list[dict[str, Any]] | None:
        """
        Calls GET /api/v1/lessons/{lesson_slug}/exercises
        Returns list of coding exercises:
        [{ "id": "...", "lesson_id": "...", "title": "...", "description": "...", "has_attachment": bool }, ...]
        Returns None if not found (404).
        """
        url = f"{self.base_url}/api/v1/lessons/{lesson_slug}/exercises"
        try:
            async with httpx.AsyncClient(
                timeout=5.0, headers=self._get_headers()
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        if "exercises" in data and isinstance(data["exercises"], list):
                            return data["exercises"]
                        if "data" in data:
                            inner = data["data"]
                            if isinstance(inner, dict) and "exercises" in inner:
                                return inner["exercises"]
                            elif isinstance(inner, list):
                                return inner
                    elif isinstance(data, list):
                        return data
                    return []
                elif response.status_code == 404:
                    logger.info(
                        f"Quiz lesson '{lesson_slug}' exercises not found (404) at {url}"
                    )
                    return None
                else:
                    logger.warning(
                        f"Quiz lesson exercises request failed: status={response.status_code}, url={url}"
                    )
        except Exception as exc:
            err_msg = str(exc) or repr(exc)
            logger.error(
                f"Error calling Quiz lesson exercises ({url}): {type(exc).__name__} - {err_msg}"
            )

        return []

    async def get_lesson_metadata(self, lesson_slug: str) -> dict[str, Any] | None:
        """
        Calls GET /api/v1/lessons/{lesson_slug}/metadata
        Returns lesson readiness metadata:
        { "slug": "...", "name": "...", "has_coding": bool, "has_game": bool, "coding_count": int, "game_question_count": int, "is_ready": bool }
        Returns None if lesson not found (404).
        Raises exception on system/network errors so they can be handled by global 500 handler.
        """
        url = f"{self.base_url}/api/v1/lessons/{lesson_slug}/metadata"
        try:
            async with httpx.AsyncClient(
                timeout=5.0, headers=self._get_headers()
            ) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, dict):
                        return data.get("data", data)
                    return data
                elif response.status_code == 404:
                    logger.info(f"Quiz lesson '{lesson_slug}' not found (404) at {url}")
                    return None
                else:
                    logger.error(
                        f"Quiz service returned unexpected status {response.status_code} for URL {url}: {response.text}"
                    )
                    raise RuntimeError(
                        f"Quiz service error: status {response.status_code}"
                    )
        except httpx.RequestError as exc:
            logger.exception(f"Connection failure to Quiz service at {url}: {exc}")
            raise RuntimeError(f"Cannot connect to Quiz service at {url}") from exc
