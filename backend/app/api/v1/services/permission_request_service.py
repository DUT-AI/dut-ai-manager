from typing import List, Optional

from loguru import logger

from app.api.v1.repositories.permission_request_repository import (
    PermissionRequestRepository,
)
from app.models.permission_request import PermissionRequest
from app.schemas.permission_request import (
    PermissionRequestCreate,
    PermissionRequestUpdate,
)


class PermissionRequestService:
    def __init__(self, repository: PermissionRequestRepository):
        self.repository = repository

    def get_all(self, skip: int = 0, limit: int = 100) -> List[PermissionRequest]:
        return self.repository.get_all(skip=skip, limit=limit)

    def get_by_id(self, request_id: int) -> Optional[PermissionRequest]:
        return self.repository.get_by_id(request_id)

    def get_by_user(
        self, month: int | None = None, year: int | None = None
    ) -> List[PermissionRequest]:
        return self.repository.get_by_month(month=month, year=year)

    def get_by_date(self, target_date) -> List[PermissionRequest]:
        return self.repository.get_by_date(target_date)

    def create(self, data: PermissionRequestCreate) -> PermissionRequest:

        request = PermissionRequest(**data.model_dump())
        return self.repository.create(request)

    def update(
        self, request_id: int, data: PermissionRequestUpdate
    ) -> Optional[PermissionRequest]:
        request = self.repository.get_by_id(request_id)
        if not request:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(request, key, value)

        return self.repository.update(request)

    def delete(self, request_id: int) -> bool:
        return self.repository.delete_by_id(request_id)
