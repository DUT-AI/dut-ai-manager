from datetime import datetime

import httpx
from loguru import logger

from app.core.config import settings
from app.shared.domain.base_entity import BaseEntity


class Homework(BaseEntity):
    """Domain model containing assignment details."""

    title: str
    deadline: datetime
    link: str | None = None
    slug: str | None = None
    assignee_ids: list[int] = []

    async def notify_external_homework_api(self) -> None:
        """Fire-and-forget POST to external homework service."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    settings.HOMEWORK_CHECKER_API_URL,
                    json={
                        "homework_link": self.link or "",
                        "homework_id": str(self.id),
                    },
                )
                logger.info(
                    f"External homework API response: status={response.status_code}, body={response.text}"
                )

        except Exception as exc:
            logger.warning(
                f"Failed to notify external homework API: {exc}", exc_info=True
            )


Homework.model_rebuild()
