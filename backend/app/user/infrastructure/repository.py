"""
User Repository — infrastructure layer.
"""

from typing import cast

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, joinedload

from app.rbac.infrastructure.model import RoleModel, RolePermissionModel
from app.shared.infrastructure.base_repository import BaseRepository
from app.user.domain.entity import UserEntity, UserStatus
from app.user.infrastructure.model import UserModel


class UserRepository(BaseRepository[UserModel, UserEntity]):
    def __init__(self, session: Session):
        super().__init__(session, UserModel)

    def add(self, entity: UserEntity) -> UserEntity:
        """Add user with eager loading of role/permissions to avoid N+1."""
        model = UserModel.from_entity(entity)
        self.session.add(model)
        self.session.flush()

        # Refresh with full details to avoid N+1 when calling to_entity()
        statement = self._get_base_query().where(UserModel.id == model.id)
        refreshed_model = self.session.scalars(statement).unique().first()

        if not refreshed_model:
            raise Exception("Failed to find user after adding")

        return refreshed_model.to_entity()

    def update(self, entity: UserEntity) -> UserEntity:
        """Update user with eager loading of role/permissions to avoid N+1."""
        model = UserModel.from_entity(entity)
        self.session.merge(model)
        self.session.flush()

        # Refresh with full details to avoid N+1 when calling to_entity()
        statement = self._get_base_query().where(UserModel.id == model.id)
        refreshed_model = cast(
            UserModel, self.session.scalars(statement).unique().first()
        )

        return refreshed_model.to_entity()

    def _get_base_query(self):
        """Query với role và toàn bộ permission (tránh N+1 khi to_entity)."""
        return select(UserModel).options(
            joinedload(UserModel.role)
            .joinedload(RoleModel.role_permissions)
            .joinedload(RolePermissionModel.permission)
        )

    def get_by_id(self, id: int) -> UserEntity | None:
        # Implementation in BaseRepository is too simple (no eager loading)
        statement = self._get_base_query().where(UserModel.id == id)
        model = self.session.scalars(statement).unique().first()
        return model.to_entity() if model else None

    def get_by_ids(self, ids: list[int]) -> list[UserEntity]:
        if not ids:
            return []
        statement = self._get_base_query().where(UserModel.id.in_(ids))
        models = self.session.scalars(statement).unique().all()
        return [m.to_entity() for m in models]

    def search_user(self, keyword: str) -> list[UserEntity]:
        statement = self._get_base_query().where(
            or_(
                UserModel.name.ilike(f"%{keyword}%"),
                UserModel.email.ilike(f"%{keyword}%"),
            )
        )
        models = self.session.scalars(statement).unique().all()
        return [m.to_entity() for m in models]

    def get_by_zalo_bind_code(self, bind_code: str) -> UserEntity | None:
        statement = self._get_base_query().where(UserModel.zalo_bind_code == bind_code)
        model = self.session.scalars(statement).unique().first()
        return model.to_entity() if model else None

    def get_by_check_in_card_code(self, code: str) -> UserEntity | None:
        statement = self._get_base_query().where(UserModel.check_in_card_code == code)
        model = self.session.scalars(statement).unique().first()
        return model.to_entity() if model else None

    def get_active_users(self) -> list[UserEntity]:
        statement = self._get_base_query().where(
            UserModel.status == UserStatus.ACTIVE,
            UserModel.is_deleted.is_(False),
        )
        models = self.session.scalars(statement).unique().all()
        return [m.to_entity() for m in models]
