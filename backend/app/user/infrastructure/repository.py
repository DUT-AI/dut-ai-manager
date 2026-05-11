"""
User Repository — infrastructure layer.
"""

from typing import List, Optional, Any, cast

from app.rbac.infrastructure.model import RoleModel, RolePermissionModel
from app.user.domain.entity import UserEntity
from app.user.infrastructure.model import UserModel
from sqlalchemy.orm import joinedload
from sqlmodel import Session, or_, select
from app.shared.infrastructure.base_repository import BaseRepository


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
        refreshed_model = self.session.exec(statement).unique().first()

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
        refreshed_model: UserModel = self.session.exec(statement).unique().first()

        return refreshed_model.to_entity()

    def _get_base_query(self) -> Any:
        """Query với role và toàn bộ permission (tránh N+1 khi to_entity)."""
        return select(UserModel).options(
            joinedload(cast(Any, UserModel.role))
            .joinedload(cast(Any, RoleModel.role_permissions))
            .joinedload(cast(Any, RolePermissionModel.permission))
        )

    def get_by_id(self, id: int) -> Optional[UserEntity]:
        # Implementation in BaseRepository is too simple (no eager loading)
        statement = self._get_base_query().where(UserModel.id == id)
        model = self.session.exec(statement).unique().first()
        return model.to_entity() if model else None

    def get_by_ids(self, ids: List[int]) -> List[UserEntity]:
        if not ids:
            return []
        statement = self._get_base_query().where(cast(Any, UserModel.id).in_(ids))
        models = self.session.exec(statement).unique().all()
        return [m.to_entity() for m in models]

    def search_user(self, keyword: str) -> List[UserEntity]:
        statement = self._get_base_query().where(
            or_(
                cast(Any, UserModel.name).ilike(f"%{keyword}%"),
                cast(Any, UserModel.email).ilike(f"%{keyword}%"),
            )
        )
        models = self.session.exec(statement).unique().all()
        return [m.to_entity() for m in models]

    def get_by_zalo_bind_code(self, bind_code: str) -> Optional[UserEntity]:
        statement = self._get_base_query().where(UserModel.zalo_bind_code == bind_code)
        model = self.session.exec(statement).unique().first()
        return model.to_entity() if model else None

    def get_by_check_in_card_code(self, code: str) -> Optional[UserEntity]:
        statement = self._get_base_query().where(UserModel.check_in_card_code == code)
        model = self.session.exec(statement).unique().first()
        return model.to_entity() if model else None

    def get_active_users(self) -> List[UserEntity]:
        from app.user.domain.entity import UserStatus
        statement = self._get_base_query().where(
            cast(Any, UserModel.status) == UserStatus.ACTIVE,
            cast(Any, UserModel.is_deleted).is_(False),
        )
        models = self.session.exec(statement).unique().all()
        return [m.to_entity() for m in models]
