from datetime import date, timedelta

from fastapi import status

from app.meeting.domain.entity import Meeting
from app.meeting.infrastructure.repository import MeetingRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.application.response import BadRequestException
from app.shared.domain.query_support import FilterCriterion, FilterOperator


class GetMeetingsUseCase:
    """Lấy danh sách các buổi họp với bộ lọc"""

    def __init__(self, repo: MeetingRepository):
        self.repo = repo

    def execute(
        self,
        skip: int = 0,
        limit: int = 100,
        start_date: date | None = None,
        end_date: date | None = None,
        deleted: bool = False,
    ) -> list[Meeting]:
        filters = []
        if start_date:
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.GTE, value=start_date
                )
            )
        if end_date:
            next_day = end_date + timedelta(days=1)
            filters.append(
                FilterCriterion(
                    field="start_time", operator=FilterOperator.LT, value=next_day
                )
            )

        qs = build_query_support(
            skip=skip,
            limit=limit,
            filters=filters,
            sort_by="start_time",
            descending=True,
        )
        return self.repo.get_all_with_participants(query_support=qs, deleted=deleted)

    def get_by_id(self, meeting_id: int) -> Meeting:
        meeting = self.repo.get_with_participants(meeting_id)
        if not meeting:
            raise BadRequestException(
                "Không tìm thấy buổi họp", status_code=status.HTTP_404_NOT_FOUND
            )
        return meeting
