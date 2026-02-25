from typing import List
from typing import Optional

from app.api.v1.repositories import BaseRepository
from app.models import User
from app.models.role import Role
from app.models.role_permission import RolePermission
from app.models.permission import Permission
from sqlalchemy.orm import joinedload
from sqlmodel import Session, select


class UserRepository(BaseRepository[User]):
    """Repository for User operations"""

    def __init__(self, session: Session):
        super().__init__(session, User)

    def get_by_id_with_role(self, user_id: int) -> Optional[User]:
        """Get user by ID with role and permissions eagerly loaded"""
        statement = (
            select(User)
            .where(User.is_deleted == False)
            .where(User.id == user_id)
            .options(
                joinedload(User.role)
                .joinedload(Role.role_permissions)
                .joinedload(RolePermission.permission)
            )
        )
        return self.session.exec(statement).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email with role and permissions eagerly loaded"""
        statement = (
            select(User)
            .where(User.is_deleted == False)
            .where(User.email == email)
            .options(
                joinedload(User.role)
                .joinedload(Role.role_permissions)
                .joinedload(RolePermission.permission)
            )
        )
        return self.session.exec(statement).first()

    def get_by_account_id(self, account_id: int) -> Optional[User]:
        """Get user by account ID with role eagerly loaded"""
        statement = (
            select(User)
            .where(User.is_deleted == False)
            .where(User.account_id == account_id)
            .options(
                joinedload(User.role)
                .joinedload(Role.role_permissions)
                .joinedload(RolePermission.permission)
            )
        )
        return self.session.exec(statement).first()

    def search_user(self, keyword: str) -> List[User]:
        """Search user by name"""
        statement = (
            select(User)
            .where(User.is_deleted == False)
            .where(User.name.contains(keyword))
        )
        return self.session.exec(statement).all()

    def get_by_zalo_bind_code(self, bind_code: str) -> Optional[User]:
        """Get user by zalo bind code"""
        statement = (
            select(User)
            .where(User.is_deleted == False)
            .where(User.zalo_bind_code == bind_code)
        )
        return self.session.exec(statement).first()
