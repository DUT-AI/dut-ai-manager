from fastapi import HTTPException
from loguru import logger

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator
from app.user.domain.entity import UserEntity
from app.user.infrastructure.repository import UserRepository


class UpdateUserUseCase:
    """Use case for updating user information."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int, **update_data) -> UserEntity:
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ],
            include=[
                "roles",
                "roles.role_permissions",
                "roles.role_permissions.permission",
            ],
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if "check_in_card_code" in update_data:
            raw = update_data["check_in_card_code"]
            if raw is None or (isinstance(raw, str) and not raw.strip()):
                update_data["check_in_card_code"] = None
            else:
                code = raw.strip()
                update_data["check_in_card_code"] = code
                qs_check = build_query_support(
                    filters=[
                        FilterCriterion(
                            field="check_in_card_code",
                            operator=FilterOperator.EQ,
                            value=code,
                        )
                    ]
                )
                other = self.repo.get_one(qs_check)
                if other and other.id != user_id:
                    raise HTTPException(
                        status_code=400,
                        detail="Mã thẻ check-in đã được người khác sử dụng",
                    )

        # Update entity with new data
        updated_entity = user.model_copy(update=update_data)

        # Save through repository
        result = self.repo.update(updated_entity)
        if not result:
            raise HTTPException(status_code=500, detail="Failed to update user")

        logger.info(f"Updated user id={user_id}")
        return result
