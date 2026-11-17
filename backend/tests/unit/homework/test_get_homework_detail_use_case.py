import pytest

from app.homework.application.get_homework_detail_use_case import (
    GetHomeworkDetailUseCase,
)
from app.homework.domain.entity import Homework
from tests.fixtures.homework_fixtures import (
    InMemoryHomeworkAssigneeRepository,
    InMemoryHomeworkExerciseRepository,
    InMemoryHomeworkRepository,
    make_exercise,
)


@pytest.mark.asyncio
async def test_get_homework_detail_returns_official_active_exercises_from_repo(
    in_memory_homework_repo: InMemoryHomeworkRepository,
    in_memory_assignee_repo: InMemoryHomeworkAssigneeRepository,
    in_memory_exercise_repo: InMemoryHomeworkExerciseRepository,
):
    """GetHomeworkDetailUseCase đọc danh mục bài con chính thức từ HomeworkExerciseRepositoryPort (chỉ active)."""
    in_memory_homework_repo.save(
        Homework(
            id=79,
            title="Gen2: Đại số tuyến tính",
            slug="dai-so-tuyen-tinh",
            requires_coding=True,
            requires_game=True,
        )
    )
    in_memory_exercise_repo.add(make_exercise(79, "ex-2", title="Bài tập 2", order_index=2, is_active=True))
    in_memory_exercise_repo.add(make_exercise(79, "ex-1", title="Bài tập 1", order_index=1, is_active=True))
    in_memory_exercise_repo.add(make_exercise(79, "ex-old", title="Bài cũ đã gỡ", order_index=3, is_active=False))

    use_case = GetHomeworkDetailUseCase(
        homework_repo=in_memory_homework_repo,
        homework_assignee_repo=in_memory_assignee_repo,
        homework_exercise_repo=in_memory_exercise_repo,
    )

    result = await use_case.execute(79)

    assert result is not None
    assert result.id == 79
    assert len(result.coding_exercises) == 2
    assert [e.exercise_id for e in result.coding_exercises] == ["ex-1", "ex-2"]
    assert result.coding_exercises[0].title == "Bài tập 1"
    assert result.coding_exercises[1].title == "Bài tập 2"
