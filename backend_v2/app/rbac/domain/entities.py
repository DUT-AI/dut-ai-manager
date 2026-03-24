from datetime import datetime
from typing import Optional

from app.shared.base_entity import BaseEntity


class Permission(BaseEntity):
    name: str
    description: Optional[str] = None
    resource: str
    action: str


class Role(BaseEntity):
    name: str
    description: Optional[str] = None
    permissions: list[Permission] = []


class RoleApiKey(BaseEntity):
    name: str
    key_hash: str
    prefix: str
    is_active: bool = True
    role_id: int

    @property
    def is_valid(self) -> bool:
        return self.is_active and not self.is_deleted
