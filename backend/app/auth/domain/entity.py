"""
Auth Domain Entity — pure Pydantic, NO ORM dependency.
"""

from app.shared.domain.base_entity import BaseEntity


class Account(BaseEntity):
    """Domain entity representing a user's authentication account."""

    hash_password: str
    user_id: int | None = None
