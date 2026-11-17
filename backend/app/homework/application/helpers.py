"""
Homework Quiz Helper — application layer helper service.

Shared utilities for slug extraction across Homework use cases.
"""

from app.homework.domain.entity import Homework as HomeworkEntity


class QuizSubmissionHelper:
    """Shared slug extraction helper for Homework use cases."""

    @staticmethod
    def extract_slug(link: str | None, slug: str | None) -> str | None:
        """Extract slug from explicit slug field or parse from URL link."""
        return HomeworkEntity.extract_slug(link, slug)

    @classmethod
    def extract_slug_from_entity(cls, homework: HomeworkEntity) -> str | None:
        """Extract slug from a Homework entity via effective_slug."""
        return homework.effective_slug
