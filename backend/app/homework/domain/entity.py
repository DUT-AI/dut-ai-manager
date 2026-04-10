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

    is_pass: Optional[bool] = None
    score: Optional[float] = None
    feedback: Optional[str] = None
    score_details: Optional[List[dict]] = None
    plagiarism_info: Optional[List[dict]] = None
    is_plagiarized: bool = False
    plagiarized_from_user_id: Optional[int] = None

    # Read-only attributes mapped from user relation
    user_name: Optional[str] = None
    user_avatar: Optional[str] = None
    homework: Optional["Homework"] = None

    def update_grading_result(
        self,
        is_pass: bool,
        score: Optional[float],
        feedback: Optional[str],
        score_details: List[dict],
        plagiarism_info: List[dict]
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
                logger.info(
                    f"External homework API response: status={response.status_code}, body={response.text}"
                )

        except Exception as exc:
            logger.warning(
                f"Failed to notify external homework API: {exc}", exc_info=True
            )


HomeworkSubmission.model_rebuild()
Homework.model_rebuild()
