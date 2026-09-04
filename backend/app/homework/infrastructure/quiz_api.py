from typing import Any

import httpx
from loguru import logger

from app.core.config import settings


class QuizApiClient:
    """Infrastructure client for interacting with the external Quiz API system."""

    def __init__(self, base_url: str | None = None, api_token: str | None = None):
        self.base_url = (base_url or settings.QUIZ_API_URL).rstrip("/")
        self.api_token = api_token or getattr(settings, "QUIZ_API_TOKEN", "")

    def _get_headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_token:
            headers["Authorization"] = f"Bearer {self.api_token}"
        return headers

    async def get_game_leaderboard(self, game_slug: str) -> list[dict[str, Any]]:
        """
        Calls GET /api/v1/game/{game_slug}/leaderboard
        Returns list of leaderboard entries:
        [{ "user_id": 24, "username": "...", "final_score": 135.0, "is_completed": true, "total_questions": 15, "answered_questions": 15 }]
        """
        url = f"{self.base_url}/api/v1/game/{game_slug}/leaderboard"
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=self._get_headers()) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        return data
                    elif isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
                        return data["data"]
                    logger.warning(f"Unexpected response structure from {url}: {data}")
                else:
                    logger.warning(
                        f"Quiz game leaderboard request failed: status={response.status_code}, url={url}"
                    )
        except Exception as exc:
            logger.error(f"Error calling Quiz game leaderboard API ({url}): {exc}")

        return []

    async def get_homework_completed_members(
        self, homework_slug: str
    ) -> list[dict[str, Any]]:
        """
        Calls GET /api/v1/homeworks/{homework_slug}/completed-members
        Returns list of completed member entries:
        [{ "user_id": 4, "submission_count": 2, "max_score": 100.0 }, ...]
        """
        url = f"{self.base_url}/api/v1/homeworks/{homework_slug}/completed-members"
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=self._get_headers()) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    res_json = response.json()
                    if isinstance(res_json, dict) and "data" in res_json and isinstance(res_json["data"], list):
                        return res_json["data"]
                    elif isinstance(res_json, list):
                        return res_json
                    logger.warning(f"Unexpected response structure from {url}: {res_json}")
                else:
                    logger.warning(
                        f"Quiz homework completed-members request failed: status={response.status_code}, url={url}"
                    )
        except Exception as exc:
            logger.error(f"Error calling Quiz completed-members API ({url}): {exc}")

        return []

    async def get_user_quiz_summary(self, user_id: int) -> dict[str, Any]:
        """
        Calls GET /api/v1/users/{user_id}/quiz-report
        Returns summary of games and homeworks completed by specific user.
        """
        url = f"{self.base_url}/api/v1/users/{user_id}/quiz-report"
        try:
            async with httpx.AsyncClient(timeout=30.0, headers=self._get_headers()) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    res_json = response.json()
                    if isinstance(res_json, dict):
                        return res_json.get("data", res_json)
                else:
                    logger.warning(
                        f"Quiz user summary request failed: status={response.status_code}, url={url}"
                    )
        except Exception as exc:
            logger.error(f"Error calling Quiz user summary API ({url}): {exc}")

        return {}
