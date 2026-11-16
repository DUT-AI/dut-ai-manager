from datetime import datetime

from app.homework.domain.entity import Homework as HomeworkEntity
from app.homework.domain.ports import HomeworkRepositoryPort


class InMemoryHomeworkRepository(HomeworkRepositoryPort):
    """Cài đặt In-Memory của HomeworkRepositoryPort phục vụ kiểm thử nhanh và độc lập."""

    def __init__(self, initial_items: list[HomeworkEntity] | None = None) -> None:
        self._storage: dict[int, HomeworkEntity] = {}
        self._next_id: int = 1
        if initial_items:
            for item in initial_items:
                self.save(item)

    def add(self, homework: HomeworkEntity) -> HomeworkEntity:
        """Alias cho create/save phục vụ fixture kiểm thử tiện lợi."""
        return self.save(homework)

    def get_all(
        self,
        deleted: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[HomeworkEntity]:
        items = [
            h for h in self._storage.values()
            if (h.is_deleted if hasattr(h, "is_deleted") else False) == deleted
        ]
        start = offset or 0
        if limit is not None:
            return items[start:start + limit]
        return items[start:]

    def get_paged(
        self, page: int = 1, page_size: int = 10, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int, dict[int, datetime | None]]:
        all_items = self.get_all(deleted=deleted)
        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        items = all_items[start:end]
        deadlines: dict[int, datetime | None] = {h.id: None for h in items if h.id}
        return items, total, deadlines

    def get_assigned_to_user_paged(
        self, user_id: int, page: int = 1, page_size: int = 10, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], int, dict[int, datetime | None]]:
        all_items = self.get_all(deleted=deleted)
        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        items = all_items[start:end]
        deadlines: dict[int, datetime | None] = {h.id: None for h in items if h.id}
        return items, total, deadlines

    def get_all_assigned_to_user(
        self, user_id: int, deleted: bool = False
    ) -> tuple[list[HomeworkEntity], dict[int, datetime | None]]:
        items = self.get_all(deleted=deleted)
        deadlines: dict[int, datetime | None] = {h.id: None for h in items if h.id}
        return items, deadlines

    def get_by_id(self, homework_id: int) -> HomeworkEntity | None:
        return self._storage.get(homework_id)

    def get_by_slug(self, slug: str) -> HomeworkEntity | None:
        target = slug.strip().lower()
        for hw in self._storage.values():
            if hw.slug and hw.slug.strip().lower() == target:
                return hw
            if hw.effective_slug and hw.effective_slug.strip().lower() == target:
                return hw
        return None

    def create(self, homework: HomeworkEntity) -> HomeworkEntity:
        if homework.id is None:
            homework = homework.model_copy(update={"id": self._next_id})
            self._next_id += 1
        assert homework.id is not None
        self._storage[homework.id] = homework
        return homework

    def update(self, homework: HomeworkEntity) -> HomeworkEntity | None:
        if homework.id is None or homework.id not in self._storage:
            return None
        self._storage[homework.id] = homework
        return homework

    def save(self, homework: HomeworkEntity) -> HomeworkEntity:
        if homework.id is None or homework.id not in self._storage:
            return self.create(homework)
        self._storage[homework.id] = homework
        return homework

    def delete(self, homework_id: int) -> bool:
        if homework_id in self._storage:
            hw = self._storage[homework_id]
            self._storage[homework_id] = hw.model_copy(update={"is_deleted": True})
            return True
        return False

    def delete_by_id(self, homework_id: int) -> bool:
        return self._storage.pop(homework_id, None) is not None
