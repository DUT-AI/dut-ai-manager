"""
Shared Pytest Fixtures for Homework In-Memory Testing.
Provides isolated, clean in-memory repositories and test doubles for zero-mock unit testing.
"""

from typing import Any, TypeVar

import pytest

from app.homework.infrastructure.in_memory import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkRepository,
    InMemoryHomeworkSubmissionRepository,
)
from app.shared.domain.event_bus import DomainEvent

T = TypeVar("T", bound=DomainEvent)


class FakeQuizApiClient:
    """Fake QuizApiClient returning controllable exercise metadata in RAM without network I/O."""

    def __init__(
        self,
        exercises: list[dict[str, Any]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._exercises_by_slug: dict[str, list[dict[str, Any]]] = {}
        self._metadata_by_slug: dict[str, dict[str, Any]] = {}
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

    async def get_lesson_exercises(self, slug: str) -> list[dict[str, Any]] | None:
        if self.should_fail:
            raise ConnectionError(f"Simulated network error for quiz api slug='{slug}'")
        if slug in self._exercises_by_slug:
            return self._exercises_by_slug[slug]
        return self.default_exercises if self.default_exercises else None

    async def get_lesson_metadata(self, slug: str) -> dict[str, Any] | None:
        if self.should_fail:
            raise ConnectionError(f"Simulated network error for metadata slug='{slug}'")
        if slug in self._metadata_by_slug:
            return self._metadata_by_slug[slug]
        meta = dict(self.default_metadata)
        meta.setdefault("slug", slug)
        return meta


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
