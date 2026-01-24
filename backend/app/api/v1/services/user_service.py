from typing import List, Optional, Tuple
from app.core.minio_service import MinioService
from fastapi import UploadFile
from app.utils.datetime import get_current_utc7_time
from app.api.v1.repositories import UserRepository
from app.api.v1.services.auth_service import AuthService
from app.models import User, RoleType
from app.schemas.response import BadRequestException
from app.schemas.user import UserCreate, UserUpdate, UserSettingsUpdate


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        auth_service: AuthService,
        minio_service: MinioService,
    ):
        self.user_repo = user_repo
        self.auth_service = auth_service
        self.minio_service = minio_service

    async def update_avatar(self, user_id: int, file: UploadFile) -> User:
        user = self.get_user_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")

        # Upload to MinIO
        file_content = await file.read()
        now = get_current_utc7_time()
        timestamp = now.strftime("%Y%m%d_%H%M%S")

        # Extension handling
        ext = "jpg"
        if file.filename and "." in file.filename:
            ext = file.filename.split(".")[-1]

        filename = f"avatars/{user_id}_{timestamp}.{ext}"

        avatar_url = self.minio_service.upload_file(
            file_data=file_content,
            filename=filename,
            content_type=file.content_type or "image/jpeg",
        )

        # Update user
        user.avatar_url = avatar_url
        return self.user_repo.update(user)

    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID with role eagerly loaded"""
        return self.user_repo.get_by_id_with_role(user_id)

    def get_all_users(self) -> List[User]:
        return self.user_repo.get_all()

    def get_system(self) -> User:
        return self.user_repo.search_user("Hệ thống")[0]

    def search_user(self, keyword: str) -> List[User]:
        return self.user_repo.search_user(keyword)

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")
        return user

    def create_user(self, user_data: UserCreate) -> Optional[User]:
        # Check email exists
        if self.user_repo.get_by_email(user_data.email):
            raise BadRequestException("Email already exists")

        # Use phone_number as password if password is not provided
        password = user_data.phone_number
        if not password:
            raise BadRequestException("Phone Number is required")

        account = self.auth_service.create_account(password)

        user = User(
            name=user_data.name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            status=user_data.status,
            role_id=user_data.role_id,
            account_id=account.id,
        )
        return self.user_repo.create(user)

    def update_user(
        self, user_id: int, user_data: UserUpdate, current_user: User
    ) -> Optional[User]:

        user = self.get_user_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")

        update_dict = user_data.model_dump(exclude_unset=True)

        # Only admin can update role_id
        if "role_id" in update_dict and current_user.role.name != RoleType.ADMIN:
            raise BadRequestException("Only admin can update role")

        # Update other fields
        for key, value in update_dict.items():
            setattr(user, key, value)

        return self.user_repo.update(user)

    def delete_user(self, user_id: int) -> bool:
        user = self.get_user_by_id(user_id)

        # Delete account too
        if user.account_id:
            self.auth_service.delete_account(user.account_id)

        return self.user_repo.delete_by_id(user_id)

    def update_settings(
        self, user_id: int, settings_data: UserSettingsUpdate
    ) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")

        update_dict = settings_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(user, key, value)

        return self.user_repo.update(user)
