import httpx
from typing import Dict, Any

from app.core.config import settings


class HomeworkGradingService:
    """Infrastructure service to interact with external grading API."""

    @staticmethod
    async def fetch_grading(
        file_url: str, homework_id: int, user_id: int
    ) -> Dict[str, Any]:
        """Calls external API and returns the raw dict containing grading data."""
        url = settings.SUBMISSION_CHECKER_API_URL

        async with httpx.AsyncClient(timeout=300.0) as client:
            payload = {
                "submission_link": file_url,
                "homework_id": str(homework_id),
                "user_id": str(user_id),
            }
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
