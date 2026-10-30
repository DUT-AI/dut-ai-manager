from app.permission_request.domain.entity import PermissionRequest
from app.permission_request.domain.value_objects import RequestCategory
from app.permission_request.infrastructure.repository import PermissionRequestRepository
from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator


class GetPermissionRequestsUseCase:
    """Lấy danh sách các yêu cầu xin phép"""

    def __init__(self, repo: PermissionRequestRepository):
        self.repo = repo

    def execute(
        self,
        user_id: int | None = None,
        month: int | None = None,
        year: int | None = None,
        category: RequestCategory | None = None,
        page: int = 1,
        page_size: int = 20,
        deleted: bool = False,
    ) -> tuple[list[PermissionRequest], int]:
        filters = []
        if user_id:
            filters.append(
                FilterCriterion(
                    field="created_by", operator=FilterOperator.EQ, value=user_id
                )
            )
        if month:
            filters.append(
                FilterCriterion(
                    field="created_at", operator=FilterOperator.MONTH_EQ, value=month
                )
            )
        if year:
            filters.append(
                FilterCriterion(
                    field="created_at", operator=FilterOperator.YEAR_EQ, value=year
                )
            )
        if category:
            filters.append(
                FilterCriterion(
                    field="category", operator=FilterOperator.EQ, value=category
                )
            )

        qs = build_query_support(
            page=page,
            page_size=page_size,
            sort_by="updated_at" if deleted else "created_at",
            descending=True,
            filters=filters,
        )
        return self.repo.get_paged(query_support=qs, deleted=deleted)
