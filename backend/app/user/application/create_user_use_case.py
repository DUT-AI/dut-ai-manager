from fastapi import BackgroundTasks, HTTPException

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.event_bus import EventBus
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.application.dtos import UserCreate
from app.user.domain.entity import UserEntity, UserStatus
from app.user.domain.events import UserCreated
from app.user.infrastructure.repository import UserRepository


class CreateUserUseCase:
    """Use case for creating a new user with account and email."""

    def __init__(
        self,
        repo: UserRepository,
    ):
        self.repo = repo

    async def execute(
        self, user_data: UserCreate, background_tasks: BackgroundTasks
    ) -> UserEntity:
        # Check email exists
        qs_email = build_query_support(
            filters=[
                FilterCriterion(
                    field="email", operator=FilterOperator.EQ, value=user_data.email
                )
            ]
        )
        if self.repo.get_one(qs_email):
            raise HTTPException(status_code=400, detail="Email already exists")

        # 1. Build & Save User Domain Entity
        new_user = UserEntity(
            name=user_data.name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            status=(
                UserStatus(user_data.status) if user_data.status else UserStatus.ACTIVE
            ),
            role_ids=user_data.role_ids,
        )
        saved_user = self.repo.add(new_user)
        self.repo.flush()
        if not saved_user or saved_user.id is None:
            raise Exception("Failed to create user")

        # 2. Publish Domain Event
        await EventBus.publish(
            UserCreated(
                user_id=saved_user.id,
                name=saved_user.name,
                email=saved_user.email,
                role_ids=saved_user.role_ids,
            )
        )

        return saved_user
