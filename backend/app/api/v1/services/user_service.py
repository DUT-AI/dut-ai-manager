from typing import List, Optional, Tuple

from app.api.v1.repositories import UserRepository
from app.api.v1.services.auth_service import AuthService
from app.models import User
from app.schemas.response import BadRequestException
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    def __init__(self, user_repo: UserRepository, auth_service: AuthService):
        self.user_repo = user_repo
        self.auth_service = auth_service

    def get_all_users(self) -> List[User]:
        return self.user_repo.get_all()

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

    def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        user = self.get_user_by_id(user_id)
        if not user:
            raise BadRequestException("User not found")

        update_dict = user_data.model_dump(exclude_unset=True)

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
