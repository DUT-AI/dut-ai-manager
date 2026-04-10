from datetime import datetime
from typing import List, Optional

import httpx
from app.core.config import settings
from app.homework.domain.value_objects import HomeworkStatus
from app.shared.domain.base_entity import BaseEntity
from loguru import logger


class HomeworkSubmission(BaseEntity):
    """Domain model tracking user submissions to homework."""

    homework_id: int
    owner_id: int
    link: str = ""
    status: HomeworkStatus = HomeworkStatus.NOT_SUBMITTED
    is_late: bool = False

    # Read-only attributes mapped from user relation
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    homework: Optional["Homework"] = None


class Homework(BaseEntity):
    """Domain model containing assignment details."""

    title: str
    description: str
    deadline: datetime
    file_url: Optional[str] = None
    submissions: List[HomeworkSubmission] = []

    @property
    def submission_count(self) -> int:
        return len(self.submissions)

    async def notify_external_homework_api(self) -> None:
        """Fire-and-forget POST to external homework service."""
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    settings.HOMEWORK_CHECKER_API_URL,
                    json={
                        "homework_link": self.file_url or "",
                        "description": self.description,
                        "homework_id": str(self.id),
                    },
                )
                logger.info(f"External homework API response: status={response.status_code}, body={response.text}")

        except Exception as exc:
            logger.warning(
                f"Failed to notify external homework API: {exc}", exc_info=True
            )


HomeworkSubmission.model_rebuild()
Homework.model_rebuild()
