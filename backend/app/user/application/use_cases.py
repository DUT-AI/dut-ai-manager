"""
User Application Use Cases — business logic layer.
"""

from datetime import datetime
from typing import List

from app.shared.application.query_support_utils import build_query_support
from app.shared.domain.query_support import FilterCriterion, FilterOperator

# External imports for complex use cases
from app.shared.infrastructure.minio_service import MinioService
from app.user.application.dtos import UserCreate, UserImportResult
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.repository import UserRepository
from fastapi import BackgroundTasks, HTTPException, UploadFile
from loguru import logger
from app.shared.domain.event_bus import EventBus
from app.user.domain.events import UserCreated


class GetUserUseCase:
    """Use case for retrieving user information."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> UserEntity:
        # Load đầy đủ role/permissions
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ],
            include=[
                "role",
                "role.role_permissions",
                "role.role_permissions.permission",
            ],
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_all(self) -> List[UserEntity]:
        # Mặc định load đầy đủ role/permissions để to_entity chính xác
        qs = build_query_support(
            include=[
                "role",
                "role.role_permissions",
                "role.role_permissions.permission",
            ]
        )
        return self.repo.get_all(qs)

    def search(self, keyword: str) -> List[UserEntity]:
        return self.repo.search_user(keyword)


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
                "role",
                "role.role_permissions",
                "role.role_permissions.permission",
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


class DeleteUserUseCase:
    """Use case for deleting (removing) a user."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> bool:
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ]
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        self.repo.soft_delete(user)
        return True


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
            role_id=user_data.role_id,
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
                role_id=saved_user.role_id,
            )
        )

        return saved_user


class ImportUsersUseCase:
    """Use case for bulk importing users from Excel/CSV."""

    def __init__(self, create_user_uc: CreateUserUseCase, repo: UserRepository):
        self.create_user_uc = create_user_uc
        self.repo = repo

    async def execute(
        self, file: UploadFile, background_tasks: BackgroundTasks
    ) -> UserImportResult:
        from io import BytesIO

        import pandas as pd

        content = await file.read()
        try:
            is_csv = file.filename and file.filename.endswith(".csv")
            if is_csv:
                df = pd.read_csv(BytesIO(content))
            else:
                df = pd.read_excel(BytesIO(content))
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid file format: {str(e)}"
            )

        df.columns = df.columns.astype(str).str.lower()
        summary = UserImportResult(
            total=len(df), success_count=0, error_count=0, errors=[]
        )

        for index, row in df.iterrows():
            row_num = int(index) + 2
            try:
                email = str(row.get("email", "")).strip()
                name = str(row.get("name", "")).strip()

                if not email or "@" not in email:
                    summary.error_count += 1
                    summary.errors.append(f"Row {row_num}: Invalid email")
                    continue

                qs_email = build_query_support(
                    filters=[
                        FilterCriterion(
                            field="email", operator=FilterOperator.EQ, value=email
                        )
                    ]
                )
                if self.repo.get_one(qs_email):
                    summary.error_count += 1
                    summary.errors.append(f"Row {row_num}: Email exists ({email})")
                    continue

                # Mocking UserCreate for simplicity in import
                # We assume a default role_id here or from request
                user_data = UserCreate(
                    name=name, email=email, role_id=row.get("role_id")
                )
                await self.create_user_uc.execute(user_data, background_tasks)
                summary.success_count += 1
            except Exception as e:
                summary.error_count += 1
                error_msg = f"Row {row_num}: {str(e)}"
                summary.errors.append(error_msg)

        return summary


class UpdateAvatarUseCase:
    """Use case for uploading and setting user avatar."""

    def __init__(self, repo: UserRepository, minio: MinioService):
        self.repo = repo
        self.minio = minio

    async def execute(self, user_id: int, file: UploadFile) -> UserEntity:
        qs = build_query_support(
            filters=[
                FilterCriterion(field="id", operator=FilterOperator.EQ, value=user_id)
            ],
            include=[
                "role",
                "role.role_permissions",
                "role.role_permissions.permission",
            ],
        )
        user = self.repo.get_one(qs)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        file_content = await file.read()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ext = (
            file.filename.split(".")[-1]
            if file.filename and "." in file.filename
            else "jpg"
        )
        filename = f"avatars/{user_id}_{timestamp}.{ext}"

        avatar_url = self.minio.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=file.content_type or "image/jpeg",
        )

        # Update entity field
        updated = user.model_copy(update={"avatar_url": avatar_url})
        return self.repo.update(updated)
