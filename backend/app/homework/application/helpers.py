"""
Homework Quiz & Submission Helper — application layer helper service.

Contains shared utilities for slug extraction and Quiz API member/leaderboard parsing.
Eliminates code duplication (DRY principle) across Homework use cases.
"""

import re
from loguru import logger

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.infrastructure.quiz_api import QuizApiClient


class QuizSubmissionHelper:
    """Service hỗ trợ xử lý slug và parse bài nộp từ Quiz API dùng chung cho các Use Cases."""

    @staticmethod
    def extract_slug(link: str | None, slug: str | None) -> str | None:
        """Trích xuất slug từ thuộc tính slug hoặc parse từ URL link."""
        if slug and slug.strip():
            return slug.strip()
        if link and link.strip():
            link_clean = link.strip()
            match = re.search(r"/(?:homeworks|game|lessons)/([^/?#]+)", link_clean)
            if match:
                return match.group(1).strip()
            if link_clean.startswith("http://") or link_clean.startswith("https://"):
                candidate = link_clean.rstrip("/").split("/")[-1].split("?")[0].split("#")[0].strip()
                if candidate and len(candidate) > 1 and " " not in candidate:
                    if candidate.lower() in ("game", "homeworks", "coding"):
                        parts = [p for p in link_clean.rstrip("/").split("/") if p]
                        if len(parts) >= 2:
                            return parts[-2].strip()
                    return candidate
        return None

    @classmethod
    def extract_slug_from_entity(cls, homework: HomeworkEntity) -> str | None:
        """Trích xuất slug từ Homework entity."""
        return cls.extract_slug(homework.link, homework.slug)

    @staticmethod
    def detect_homework_type(link: str | None, slug: str | None) -> str:
        """Tự động kiểm tra cả Coding và Game; nếu mục nào Quiz API trả về 404/None sẽ tự động bỏ qua."""
        return "both"

    @staticmethod
    async def get_coding_completed_map(quiz_api: QuizApiClient | None, slug: str) -> dict[int, dict] | None:
        """Lấy bản đồ thành viên đã hoàn thành bài tập Coding theo user_id từ Quiz API."""
        if not quiz_api:
            return None
        try:
            members = await quiz_api.get_homework_completed_members(slug)
            if members is None:
                return None
            res: dict[int, dict] = {}
            for entry in members:
                if isinstance(entry, dict):
                    uid = entry.get("user_id")
                    if uid is not None and entry.get("submission_count", 1) > 0:
                        res[int(uid)] = entry
                elif isinstance(entry, (int, str)):
                    res[int(entry)] = {"user_id": int(entry)}
            return res
        except Exception as exc:
            logger.warning(f"Quiz completed-members error for slug={slug}: {exc}")
            return None

    @staticmethod
    async def get_game_completed_map(quiz_api: QuizApiClient | None, slug: str) -> dict[int, dict] | None:
        """Lấy bản đồ thành viên đã hoàn thành game theo user_id từ Quiz API."""
        if not quiz_api:
            return None
        try:
            leaderboard = await quiz_api.get_game_leaderboard(slug)
            if leaderboard is None:
                return None
            res: dict[int, dict] = {}
            for entry in leaderboard:
                if isinstance(entry, dict):
                    is_completed = entry.get("is_completed", True)
                    total_q = entry.get("total_questions")
                    ans_q = entry.get("answered_questions")
                    if total_q is not None and ans_q is not None and ans_q < total_q:
                        is_completed = False
                    uid = entry.get("user_id")
                    if is_completed and uid:
                        res[int(uid)] = entry
                elif isinstance(entry, (int, str)):
                    res[int(entry)] = {"user_id": int(entry)}
            return res
        except Exception as exc:
            logger.warning(f"Quiz leaderboard error for slug={slug}: {exc}")
            return None

    @classmethod
    async def get_coding_completed_user_ids(cls, quiz_api: QuizApiClient | None, slug: str) -> set[int] | None:
        """Lấy danh sách user_id đã hoàn thành bài tập Coding."""
        completed_map = await cls.get_coding_completed_map(quiz_api, slug)
        if completed_map is None:
            return None
        return set(completed_map.keys())

    @classmethod
    async def get_game_completed_user_ids(cls, quiz_api: QuizApiClient | None, slug: str) -> set[int] | None:
        """Lấy danh sách user_id đã hoàn thành game."""
        completed_map = await cls.get_game_completed_map(quiz_api, slug)
        if completed_map is None:
            return None
        return set(completed_map.keys())

    @staticmethod
    def is_user_submitted(
        user_id: int,
        coding_completed_uids: set[int] | None,
        game_completed_uids: set[int] | None,
    ) -> bool:
        """
        Kiểm tra xem user_id đã nộp bài tập hay chưa dựa trên kết quả từ Quiz API.
        - coding_completed_uids is None: không có phần Coding.
        - game_completed_uids is None: không có phần Game.
        - Nếu có cả 2: User phải hoàn thành CẢ 2.
        - Nếu chỉ có 1: User phải hoàn thành phần đó.
        """
        has_coding = coding_completed_uids is not None
        has_game = game_completed_uids is not None

        if has_coding and has_game:
            return (user_id in (coding_completed_uids or set())) and (user_id in (game_completed_uids or set()))
        elif has_coding:
            return user_id in (coding_completed_uids or set())
        elif has_game:
            return user_id in (game_completed_uids or set())
        else:
            return False

