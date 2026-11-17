from app.homework.domain.entity import HomeworkExercise
from app.homework.domain.ports import HomeworkExerciseRepositoryPort


class InMemoryHomeworkExerciseRepository(HomeworkExerciseRepositoryPort):
    """Cài đặt In-Memory của HomeworkExerciseRepositoryPort phục vụ kiểm thử nhanh và độc lập."""

    def __init__(
        self, initial_exercises: list[HomeworkExercise] | None = None
    ) -> None:
        self._storage: dict[tuple[int, str], HomeworkExercise] = {}
        self._next_id: int = 1
        if initial_exercises:
            for ex in initial_exercises:
                self.add(ex)

    def add(self, exercise: HomeworkExercise) -> HomeworkExercise:
        if exercise.id is None:
            exercise = exercise.model_copy(update={"id": self._next_id})
            self._next_id += 1
        self._storage[(exercise.homework_id, exercise.exercise_id)] = exercise
        return exercise

    def clear(self) -> None:
        self._storage.clear()
        self._next_id = 1

    def get_active_by_homework(self, homework_id: int) -> list[HomeworkExercise]:
        items = [
            ex
            for ex in self._storage.values()
            if ex.homework_id == homework_id and ex.is_active
        ]
        items.sort(key=lambda x: (x.order_index, x.exercise_id))
        return items

    def get_active_by_homework_ids(
        self, homework_ids: list[int]
    ) -> dict[int, list[HomeworkExercise]]:
        return {hid: self.get_active_by_homework(hid) for hid in homework_ids}

    def sync_exercises(
        self, homework_id: int, exercises: list[HomeworkExercise]
    ) -> list[HomeworkExercise]:
        incoming_ids: set[str] = set()
        for ex in exercises:
            ex_id = str(ex.exercise_id).strip()
            if not ex_id:
                continue
            incoming_ids.add(ex_id)
            key = (homework_id, ex_id)
            if key in self._storage:
                existing = self._storage[key]
                self._storage[key] = existing.model_copy(
                    update={
                        "title": ex.title,
                        "order_index": ex.order_index,
                        "is_active": True,
                    }
                )
            else:
                self.add(
                    HomeworkExercise(
                        homework_id=homework_id,
                        exercise_id=ex_id,
                        title=ex.title,
                        order_index=ex.order_index,
                        is_active=True,
                    )
                )

        for key, existing in list(self._storage.items()):
            if key[0] == homework_id and key[1] not in incoming_ids and existing.is_active:
                self._storage[key] = existing.model_copy(update={"is_active": False})

        return self.get_active_by_homework(homework_id)
