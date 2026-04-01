from datetime import datetime
from typing import Optional

from app.shared.domain.base_entity import BaseEntity
from app.shared.domain.value_objects import UserRef
from pydantic import Field


class BonusPoint(BaseEntity):
    """Bonus Point domain entity."""

    points: int
    reason: str = Field(max_length=500)
    date: datetime
    user_id: int
    owner: Optional[UserRef] = None
    creator: Optional[UserRef] = None
    updater: Optional[UserRef] = None

    @property
    def user_name(self) -> Optional[str]:
        return self.owner.name if self.owner else None

    @property
    def user_avatar(self) -> Optional[str]:
        return self.owner.avatar if self.owner else None

    @property
    def creator_name(self) -> Optional[str]:
        return self.creator.name if self.creator else None

    @property
    def updater_name(self) -> Optional[str]:
        return self.updater.name if self.updater else None
