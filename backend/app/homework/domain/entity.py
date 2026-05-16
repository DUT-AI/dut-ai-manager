from datetime import datetime
from typing import Optional

import httpx
from loguru import logger

from app.core.config import settings
from app.homework.domain.value_objects import HomeworkStatus
from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef


class HomeworkSubmission(BaseEntity):
    """Domain model tracking user submissions to homework."""

    homework_id: int
    owner_id: int
    link: str = ""
    status: HomeworkStatus = HomeworkStatus.NOT_SUBMITTED
    is_late: bool = False

    is_pass: bool | None = None
    score: float | None = None
    feedback: str | None = None
    score_details: list[dict] | None = None
    plagiarism_info: list[dict] | None = None
    is_plagiarized: bool = False
    plagiarized_from_user_id: int | None = None

    # Standardized user reference
    owner: UserRef | None = None
    homework: Optional["Homework"] = None

    def update_grading_result(
        self,
        is_pass: bool,
        score: float | None,
        feedback: str | None,
        score_details: list[dict],
        plagiarism_info: list[dict],
    ) -> None:
        """Cập nhật điểm và đánh giá đạo văn theo Business Rule."""
        self.is_pass = is_pass
        self.score = score
        self.feedback = feedback
        self.score_details = score_details
        self.plagiarism_info = plagiarism_info

        self.is_plagiarized = False
        self.plagiarized_from_user_id = None

        # Quy tắc: Similarity Score >= 0.8 => Đạo văn
        for item in plagiarism_info:
            for filename, detail in item.items():
                score_data = detail.get("score") or {}
                sim_score = score_data.get("similarity_score", 0)
                if sim_score >= 0.8:
                    self.is_plagiarized = True
                    best_match = detail.get("best_user_id_match")
                    if best_match and str(best_match).isdigit():
                        self.plagiarized_from_user_id = int(best_match)
                    break
            if self.is_plagiarized:
                break


class Homework(BaseEntity):
    """Domain model containing assignment details."""

    title: str
    description: str
    deadline: datetime
    file_url: str | None = None
    submissions: list[HomeworkSubmission] = []

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
                logger.info(
                    f"External homework API response: status={response.status_code}, body={response.text}"
                )

        except Exception as exc:
            logger.warning(
                f"Failed to notify external homework API: {exc}", exc_info=True
            )


HomeworkSubmission.model_rebuild()
Homework.model_rebuild()
