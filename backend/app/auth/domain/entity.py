"""
Auth Domain Entity — pure Pydantic, NO ORM dependency.
"""

from typing import Optional

from app.shared.domain.base_entity import BaseEntity
from pydantic import BaseModel


class Account(BaseEntity):
    """Domain entity representing a user's authentication account."""

    hash_password: str
    user_id: Optional[int] = None
