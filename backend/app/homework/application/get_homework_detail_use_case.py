from app.homework.application.dtos import (
    ExerciseSummaryDTO,
    HomeworkResponseDetail,
)
from app.homework.domain.ports import (
    HomeworkAssigneeRepositoryPort,
    HomeworkExerciseRepositoryPort,
    HomeworkRepositoryPort,
)


class GetHomeworkDetailUseCase:
    """Use case lấy thông tin chi tiết một bài tập theo ID bao gồm danh sách assignee_ids và danh mục bài tập con chính thức."""

    def __init__(
        self,
        homework_repo: HomeworkRepositoryPort,
        homework_assignee_repo: HomeworkAssigneeRepositoryPort,
        homework_exercise_repo: HomeworkExerciseRepositoryPort,
    ):
        self.homework_repo = homework_repo
        self.homework_assignee_repo = homework_assignee_repo
        self.homework_exercise_repo = homework_exercise_repo

    async def execute(self, homework_id: int) -> HomeworkResponseDetail | None:
        hw = self.homework_repo.get_by_id(homework_id)
        if not hw or not hw.id:
            return None

        assignees = self.homework_assignee_repo.get_assignees_with_user_info(
            homework_id
        )
        assignee_ids = sorted([a.user_id for a in assignees])
        deadlines = [a.deadline for a in assignees if a.deadline]
        min_dl = min(deadlines) if deadlines else None

        coding_exercises: list[ExerciseSummaryDTO] = []
        if hw.requires_coding:
            active_exercises = self.homework_exercise_repo.get_active_by_homework(hw.id)
            coding_exercises = [
                ExerciseSummaryDTO(
                    exercise_id=ex.exercise_id,
                    title=ex.title,
                    order_index=ex.order_index,
                )
                for ex in active_exercises
            ]

        return HomeworkResponseDetail.from_domain(
            hw,
            assignee_ids=assignee_ids,
            deadline=min_dl,
            coding_exercises=coding_exercises,
        )
