from sqlalchemy import select
from sqlalchemy.orm import Session

from app.homework.domain.entity import HomeworkExercise
from app.homework.domain.ports import HomeworkExerciseRepositoryPort
from app.homework.infrastructure.model import HomeworkExerciseModel


class HomeworkExerciseRepository(HomeworkExerciseRepositoryPort):
    """SQLAlchemy repository quản lý danh mục bài tập lập trình con chính thức."""

    def __init__(self, session: Session):
        self.session = session

    def get_active_by_homework(self, homework_id: int) -> list[HomeworkExercise]:
        statement = (
            select(HomeworkExerciseModel)
            .where(
                HomeworkExerciseModel.homework_id == homework_id,
                HomeworkExerciseModel.is_active == True,
            )
            .order_by(
                HomeworkExerciseModel.order_index.asc(),
                HomeworkExerciseModel.exercise_id.asc(),
            )
        )
        models = self.session.scalars(statement).all()
        return [m.to_entity() for m in models]

    def get_active_by_homework_ids(
        self, homework_ids: list[int]
    ) -> dict[int, list[HomeworkExercise]]:
        if not homework_ids:
            return {}
        statement = (
            select(HomeworkExerciseModel)
            .where(
                HomeworkExerciseModel.homework_id.in_(homework_ids),
                HomeworkExerciseModel.is_active == True,
            )
            .order_by(
                HomeworkExerciseModel.homework_id.asc(),
                HomeworkExerciseModel.order_index.asc(),
                HomeworkExerciseModel.exercise_id.asc(),
            )
        )
        models = self.session.scalars(statement).all()
        result: dict[int, list[HomeworkExercise]] = {hid: [] for hid in homework_ids}
        for model in models:
            result.setdefault(model.homework_id, []).append(model.to_entity())
        return result

    def sync_exercises(
        self, homework_id: int, exercises: list[HomeworkExercise]
    ) -> list[HomeworkExercise]:
        existing_models = self.session.scalars(
            select(HomeworkExerciseModel).where(
                HomeworkExerciseModel.homework_id == homework_id
            )
        ).all()
        existing_by_ex_id = {m.exercise_id: m for m in existing_models}

        incoming_ids: set[str] = set()
        for ex in exercises:
            ex_id = str(ex.exercise_id).strip()
            if not ex_id:
                continue
            incoming_ids.add(ex_id)
            if ex_id in existing_by_ex_id:
                model = existing_by_ex_id[ex_id]
                model.title = ex.title
                model.order_index = ex.order_index
                model.is_active = True
            else:
                self.session.add(
                    HomeworkExerciseModel(
                        homework_id=homework_id,
                        exercise_id=ex_id,
                        title=ex.title,
                        order_index=ex.order_index,
                        is_active=True,
                    )
                )

        # Deactivate exercises removed from Quiz catalog (keep historical reference)
        for ex_id, model in existing_by_ex_id.items():
            if ex_id not in incoming_ids and model.is_active:
                model.is_active = False

        self.session.flush()
        return self.get_active_by_homework(homework_id)
