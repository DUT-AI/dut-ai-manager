from pydantic import BaseModel

from app.shared.domain.value_objects import UserRef


class HomeworkReportResponse(BaseModel):
    user_id: int
    owner: UserRef | None = None
    unsubmitted_count: int = 0
