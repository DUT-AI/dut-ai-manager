"""
Shared Pytest Fixtures for Homework In-Memory Testing.
Provides isolated, clean in-memory repositories and test doubles for zero-mock unit testing.
"""

from datetime import UTC, datetime
from typing import Any, TypeVar

import pytest

from app.homework.domain.entity import (
    CodingHomeworkSubmission,
    GameHomeworkSubmission,
    HomeworkExercise,
)
from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
)
from app.shared.domain.event_bus import DomainEvent

T = TypeVar("T", bound=DomainEvent)


def make_exercise(
    homework_id: int,
    exercise_id: str,
    title: str | None = None,
    order_index: int = 1,
    is_active: bool = True,
) -> HomeworkExercise:
    """Helper factory creating a HomeworkExercise domain entity."""
    return HomeworkExercise(
        homework_id=homework_id,
        exercise_id=exercise_id,
        title=title or f"Bài tập {exercise_id}",
        order_index=order_index,
        is_active=is_active,
    )


def make_coding_submission(
    homework_id: int,
    user_id: int,
    exercise_id: str,
    submitted_at: datetime | None = None,
    is_passed: bool = True,
    external_submission_id: str | None = None,
    score: float | None = 100.0,
    attempt_number: int = 1,
) -> CodingHomeworkSubmission:
    """Helper factory creating a CodingHomeworkSubmission domain entity."""
    return CodingHomeworkSubmission.create_coding(
        homework_id=homework_id,
        user_id=user_id,
        exercise_id=exercise_id,
        submitted_at=submitted_at or datetime.now(UTC),
        is_passed=is_passed,
        external_submission_id=external_submission_id,
        score=score,
        attempt_number=attempt_number,
    )


def make_game_submission(
    homework_id: int,
    user_id: int,
    submitted_at: datetime | None = None,
    is_passed: bool = True,
    external_submission_id: str | None = None,
    score: float | None = 100.0,
) -> GameHomeworkSubmission:
    """Helper factory creating a GameHomeworkSubmission domain entity."""
    return GameHomeworkSubmission.create_game(
        homework_id=homework_id,
        user_id=user_id,
        submitted_at=submitted_at or datetime.now(UTC),
        is_passed=is_passed,
        external_submission_id=external_submission_id,
        score=score,
    )


class FakeQuizApiClient:
    """Fake QuizApiClient returning controllable exercise metadata in RAM without network I/O."""

    def __init__(
        self,
        exercises: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._exercises_by_slug: dict[str, list[dict[str, Any]]] = {}
        self._metadata_by_slug: dict[str, dict[str, Any]] = {}
        self._coding_subs_by_slug: dict[str, list[dict[str, Any]]] = {}
        self._game_sessions_by_slug: dict[str, list[dict[str, Any]]] = {}
        self.default_exercises: list[dict[str, Any]] = exercises or []
        self.default_metadata: dict[str, Any] = metadata or {
            "has_coding": True,
            "has_game": False,
        }
        self.should_fail: bool = False

    def set_lesson_exercises(self, slug: str, exercises: list[dict[str, Any]]) -> None:
        self._exercises_by_slug[slug] = exercises

    def set_lesson_metadata(self, slug: str, metadata: dict[str, Any]) -> None:
        self._metadata_by_slug[slug] = metadata

    def set_coding_submissions(
        self, slug: str, submissions: list[dict[str, Any]]
    ) -> None:
        self._coding_subs_by_slug[slug] = submissions

    def set_game_sessions(self, slug: str, sessions: list[dict[str, Any]]) -> None:
        self._game_sessions_by_slug[slug] = sessions

    async def get_lesson_exercises(self, slug: str) -> list[dict[str, Any]] | None:
        if self.should_fail:
            raise ConnectionError(
                f"Simulated network error for quiz api slug='{slug}'"
            )
        if slug in self._exercises_by_slug:
            return self._exercises_by_slug[slug]
        return self.default_exercises if self.default_exercises else None

    async def get_lesson_metadata(self, slug: str) -> dict[str, Any] | None:
        if self.should_fail:
            raise ConnectionError(
                f"Simulated network error for metadata slug='{slug}'"
            )
        if slug in self._metadata_by_slug:
            return self._metadata_by_slug[slug]
        meta = dict(self.default_metadata)
        meta.setdefault("slug", slug)
        return meta

    async def get_homework_submissions_for_sync(
        self, slug: str
    ) -> list[dict[str, Any]] | None:
        if self.should_fail:
            raise ConnectionError(
                f"Simulated network error for coding sync slug='{slug}'"
            )
        return self._coding_subs_by_slug.get(slug, [])

    async def get_game_sessions_for_sync(
        self, slug: str
    ) -> list[dict[str, Any]] | None:
        if self.should_fail:
            raise ConnectionError(
                f"Simulated network error for game sync slug='{slug}'"
            )
        return self._game_sessions_by_slug.get(slug, [])


class SpyEventBus:
    """In-memory event bus spy for capturing published domain events."""

    def __init__(self) -> None:
        self.published_events: list[DomainEvent] = []

    async def publish(self, event: DomainEvent) -> None:
        self.published_events.append(event)

    def clear(self) -> None:
        self.published_events.clear()

    def get_events_of_type(self, event_type: type[T]) -> list[T]:
        return [e for e in self.published_events if isinstance(e, event_type)]


@pytest.fixture
def in_memory_homework_repo() -> InMemoryHomeworkRepository:
    """Provides a fresh, empty InMemoryHomeworkRepository."""
    return InMemoryHomeworkRepository()


@pytest.fixture
def in_memory_exercise_repo() -> InMemoryHomeworkExerciseRepository:
    """Provides a fresh, empty InMemoryHomeworkExerciseRepository."""
    return InMemoryHomeworkExerciseRepository()


@pytest.fixture
def in_memory_submission_repo() -> InMemoryHomeworkSubmissionRepository:
    """Provides a fresh, empty InMemoryHomeworkSubmissionRepository."""
    return InMemoryHomeworkSubmissionRepository()


@pytest.fixture
def in_memory_assignee_repo() -> InMemoryHomeworkAssigneeRepository:
    """Provides a fresh, empty InMemoryHomeworkAssigneeRepository."""
    return InMemoryHomeworkAssigneeRepository()


@pytest.fixture
def fake_quiz_api() -> FakeQuizApiClient:
    """Provides a fresh FakeQuizApiClient."""
    return FakeQuizApiClient()


@pytest.fixture
def spy_event_bus() -> SpyEventBus:
    """Provides a fresh SpyEventBus."""
    return SpyEventBus()
