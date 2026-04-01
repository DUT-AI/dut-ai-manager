"""
User Repository — infrastructure layer.
"""

from typing import List, Optional

from app.rbac.infrastructure.model import RoleModel, RolePermissionModel
from app.user.domain.entity import UserEntity
from app.user.infrastructure.model import UserModel
from sqlalchemy.orm import joinedload
from sqlmodel import Session, or_, select


class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def _get_base_query(self):
        """Query với role và toàn bộ permission (tránh N+1 khi to_entity)."""
        return select(UserModel).options(
            joinedload(UserModel.role)
            .joinedload(RoleModel.role_permissions)
            .joinedload(RolePermissionModel.permission)
        )

    def get_by_id(self, user_id: int) -> Optional[UserEntity]:
        statement = self._get_base_query().where(UserModel.id == user_id)
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def get_by_email(self, email: str) -> Optional[UserEntity]:
        statement = self._get_base_query().where(UserModel.email == email)
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def get_all(self) -> List[UserEntity]:
        statement = self._get_base_query()
        models = self.session.exec(statement).all()
        return [m.to_entity() for m in models]

    def search_user(self, keyword: str) -> List[UserEntity]:
        statement = self._get_base_query().where(
            or_(
                UserModel.name.ilike(f"%{keyword}%"),
                UserModel.email.ilike(f"%{keyword}%"),
            )
        )
        models = self.session.exec(statement).all()
        return [m.to_entity() for m in models]

    def get_by_zalo_bind_code(self, bind_code: str) -> Optional[UserEntity]:
        statement = self._get_base_query().where(UserModel.zalo_bind_code == bind_code)
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def get_by_check_in_card_code(self, code: str) -> Optional[UserEntity]:
        statement = self._get_base_query().where(UserModel.check_in_card_code == code)
        model = self.session.exec(statement).first()
        return model.to_entity() if model else None

    def save(self, entity: UserEntity) -> UserEntity:
        model = UserModel.from_entity(entity)
        self.session.add(model)
        self.session.flush()
        # Refresh to get IDs and also load relationships
        self.session.refresh(model)

        # Reload with joined options to ensure entity has full data
        return self.get_by_id(model.id)  # type: ignore

    def update(self, entity: UserEntity) -> Optional[UserEntity]:
        model = self.session.get(UserModel, entity.id)
        if not model:
            return None

        update_data = entity.model_dump(
            exclude={"id", "created_at", "updated_at"}, exclude_unset=True
        )
        for key, value in update_data.items():
            if hasattr(model, key):
                setattr(model, key, value)

        self.session.add(model)
        self.session.flush()
        return self.get_by_id(model.id)  # type: ignore

    def delete_by_id(self, user_id: int) -> bool:
        model = self.session.get(UserModel, user_id)
        if not model:
            return False
        self.session.delete(model)
        self.session.flush()
        return True
