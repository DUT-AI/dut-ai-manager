from app.homework.application.dtos import (
    ExerciseSummaryDTO,
    HomeworkResponseDetail,
)
from app.homework.application.homework_exercise_resolver import (
    HomeworkExerciseResolver,
)
from app.homework.infrastructure.homework_assignee_repository import (
    HomeworkAssigneeRepository,
)
from app.homework.infrastructure.homework_repository import HomeworkRepository


class GetHomeworkDetailUseCase:
    """Use case lấy thông tin chi tiết một bài tập theo ID bao gồm danh sách assignee_ids và danh mục bài tập con."""

    def __init__(
        self,
        homework_repo: HomeworkRepository,
        homework_assignee_repo: HomeworkAssigneeRepository,
        exercise_resolver: HomeworkExerciseResolver,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.exercise_resolver = exercise_resolver

    async def execute(self, homework_id: int) -> HomeworkResponseDetail | None:
        hw = self.homework_repo.get_by_id(homework_id)
        if not hw:
            return None
        assignees = self.homework_assignee_repo.get_assignees_with_user_info(
            homework_id
        )
        assignee_ids = sorted([a.user_id for a in assignees])
        deadlines = [a.deadline for a in assignees if a.deadline]
        min_dl = min(deadlines) if deadlines else None

        coding_exercises: list[ExerciseSummaryDTO] = []
        if hw.requires_coding:
            coding_exercises = await self.exercise_resolver.get_coding_exercises(
                hw.id, hw.slug
            )

        return HomeworkResponseDetail.from_domain(
            hw,
            assignee_ids=assignee_ids,
            deadline=min_dl,
            coding_exercises=coding_exercises,
        )
