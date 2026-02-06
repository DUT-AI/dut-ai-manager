from typing import List, Optional


from app.api.v1.repositories import UserRepository, RoleRepository
from app.api.v1.services.auth_service import AuthService
from app.api.v1.services.email_service import EmailService
from app.core.minio_service import MinioService
from app.models import RoleType, User
from app.schemas.response import BadRequestException
from app.schemas.user import (
    UserCreate,
    UserSettingsUpdate,
    UserUpdate,
    UserImportResult,
)
from app.utils.datetime import get_current_utc7_time
from fastapi import UploadFile, BackgroundTasks


class UserService:
    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        auth_service: AuthService,
        minio_service: MinioService,
        email_service: EmailService,
    ):
        self.user_repo = user_repo
        self.role_repo = role_repo
        self.auth_service = auth_service
        self.minio_service = minio_service
        self.email_service = email_service

    async def import_users(
        self, file: UploadFile, background_tasks: BackgroundTasks = None
    ) -> UserImportResult:
        import pandas as pd
        from io import BytesIO

        content = await file.read()

        try:
            if file.filename.endswith(".csv"):
                df = pd.read_csv(BytesIO(content))
            else:
                df = pd.read_excel(BytesIO(content))
        except Exception as e:
            raise BadRequestException(f"Invalid file format: {str(e)}")

        # Check columns
        required_columns = ["name", "email", "phone_number"]
        # Normalize columns to lowercase
        df.columns = df.columns.astype(str).str.lower()

        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            raise BadRequestException(f"Missing columns: {', '.join(missing_cols)}")

        # Get Teammate Role
        teammate_role = self.role_repo.get_by_name(RoleType.TEAMMATE.value)
        if not teammate_role:
            raise BadRequestException("Default teammate role not found")

        summary = UserImportResult(
            total=len(df), success_count=0, error_count=0, errors=[]
        )

        for index, row in df.iterrows():
            row_num = index + 2
            try:
                # Safe get values
                email_raw = row.get("email", "")
                name_raw = row.get("name", "")
                phone_raw = row.get("phone_number", "")

                # Check for empty/NaN
                if pd.isna(email_raw) or str(email_raw).strip() == "":
                    summary.error_count += 1
                    summary.errors.append(f"Row {row_num}: Missing email address")
                    continue

                if pd.isna(name_raw) or str(name_raw).strip() == "":
                    summary.error_count += 1
                    summary.errors.append(f"Row {row_num}: Missing user name")
                    continue

                email = str(email_raw).strip()
                name = str(name_raw).strip()
                phone = (
                    str(phone_raw).strip()
                    if pd.notna(phone_raw) and str(phone_raw).strip() != ""
                    else None
                )

                # Basic email validation check
                if "@" not in email:
                    summary.error_count += 1
                    summary.errors.append(
                        f"Row {row_num}: Invalid email format ({email})"
                    )
                    continue

                user_data = UserCreate(
                    name=name, email=email, phone_number=phone, role_id=teammate_role.id
                )

                # Check email existence manually
                if self.user_repo.get_by_email(user_data.email):
                    summary.error_count += 1
                    summary.errors.append(
                        f"Row {row_num}: Email already exists ({email})"
                    )
                    continue

                self.create_user(user_data, background_tasks)
                summary.success_count += 1

            except Exception as e:
                # Simplify generic errors
                error_msg = str(e)
                if "validation error" in error_msg:
                    error_msg = "Invalid data format"

                summary.error_count += 1
                summary.errors.append(f"Row {row_num}: {error_msg}")

        return summary

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

    def create_user(
        self, user_data: UserCreate, background_tasks: BackgroundTasks = None
    ) -> Optional[User]:
        # Check email exists
        if self.user_repo.get_by_email(user_data.email):
            raise BadRequestException("Email already exists")

        account, password = self.auth_service.create_account()

        user = User(
            name=user_data.name,
            email=user_data.email,
            phone_number=user_data.phone_number,
            status=user_data.status,
            role_id=user_data.role_id,
            account_id=account.id,
        )
        new_user = self.user_repo.create(user)

        # Send email with credentials
        if background_tasks:
            background_tasks.add_task(
                self.email_service.send_new_account_email,
                to_email=new_user.email,
                name=new_user.name,
                password=password,
            )
        else:
            # Fallback for when no background task context is available
            try:
                self.email_service.send_new_account_email(
                    to_email=new_user.email, name=new_user.name, password=password
                )
            except Exception as e:
                # Log error
                print(f"Failed to send email to {new_user.email}: {e}")

        return new_user

    def update_user(
        self, user_id: int, user_data: UserUpdate, current_user: User
    ) -> Optional[User]:

        user = self.get_user_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")

        update_dict = user_data.model_dump(exclude_unset=True)

        # Only admin can update role_id
        if "role_id" in update_dict and current_user.role.name != RoleType.ADMIN.value:
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
