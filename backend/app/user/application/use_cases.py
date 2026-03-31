"""
User Application Use Cases — business logic layer.
"""

from typing import List
from datetime import datetime
from app.shared.domain.event_bus import EventBus
from app.user.domain.entity import User, UserStatus
from app.user.infrastructure.repository import UserRepository

# External imports for complex use cases
from app.api.v1.services.auth_service import AuthService
from app.api.v1.services.email_service import EmailService
from app.core.minio_service import MinioService
from app.schemas.user import UserCreate, UserImportResult
from fastapi import BackgroundTasks, UploadFile


class GetUserUseCase:
    """Use case for retrieving user information."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def get_all(self) -> List[User]:
        return self.repo.get_all()

    def search(self, keyword: str) -> List[User]:
        return self.repo.search_user(keyword)


class UpdateUserUseCase:
    """Use case for updating user information."""

    def __init__(self, repo: UserRepository):
        self.repo = repo

    def execute(self, user_id: int, **update_data) -> User:
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

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
        user = self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return self.repo.delete_by_id(user_id)


class CreateUserUseCase:
    """Use case for creating a new user with account and email."""

    def __init__(
        self,
        repo: UserRepository,
        auth_service: AuthService,
        email_service: EmailService,
    ):
        self.repo = repo
        self.auth_service = auth_service
        self.email_service = email_service

    async def execute(
        self, user_data: UserCreate, background_tasks: BackgroundTasks
    ) -> User:
        # Check email exists
        if self.repo.get_by_email(user_data.email):
            raise HTTPException(status_code=400, detail="Email already exists")

        # Create auth account
        account, password = self.auth_service.create_account()

        # Build Domain Entity
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            status=(
                UserStatus(user_data.status) if user_data.status else UserStatus.ACTIVE
            ),
            role_id=user_data.role_id,
            account_id=account.id,
        )

        # Save
        saved_user = self.repo.save(new_user)

        # Send welcome email
        background_tasks.add_task(
            self.email_service.send_new_account_email,
            to_email=saved_user.email,
            name=saved_user.name,
            password=password,
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
            if file.filename.endswith(".csv"):
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
            row_num = index + 2
            try:
                email = str(row.get("email", "")).strip()
                name = str(row.get("name", "")).strip()

                if not email or "@" not in email:
                    summary.error_count += 1
                    summary.errors.append(f"Row {row_num}: Invalid email")
                    continue

                if self.repo.get_by_email(email):
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
                summary.errors.append(f"Row {row_num}: {str(e)}")

        return summary


class UpdateAvatarUseCase:
    """Use case for uploading and setting user avatar."""

    def __init__(self, repo: UserRepository, minio: MinioService):
        self.repo = repo
        self.minio = minio

    async def execute(self, user_id: int, file: UploadFile) -> User:
        user = self.repo.get_by_id(user_id)
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
