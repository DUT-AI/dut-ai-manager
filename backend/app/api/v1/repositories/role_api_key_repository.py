from typing import Optional

from app.api.v1.repositories.base import BaseRepository
from app.models.role_api_key import RoleApiKey
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload


class RoleApiKeyRepository(BaseRepository[RoleApiKey]):
    """Repository for RoleApiKey operations"""

    def __init__(self, session: Session):
        super().__init__(session, RoleApiKey)

    def get_by_key_hash(self, key_hash: str) -> Optional[RoleApiKey]:
        """Get API key by hash"""
        statement = select(RoleApiKey).where(
            RoleApiKey.is_deleted == False,
            RoleApiKey.key_hash == key_hash,
            RoleApiKey.is_active == True,
        )
        return self.session.exec(statement).first()

    def get_by_role_id(self, role_id: int) -> list[RoleApiKey]:
        """Get all API keys for a role"""
        statement = select(RoleApiKey).where(
            RoleApiKey.is_deleted == False,
            RoleApiKey.role_id == role_id,
        )
        return list(self.session.exec(statement).all())

    def get_candidates_by_prefix(self, prefix: str) -> list[RoleApiKey]:
        """Get all active API keys with mathcing prefix"""
        statement = (
            select(RoleApiKey)
            .where(
                RoleApiKey.is_deleted == False,
                RoleApiKey.prefix == prefix,
                RoleApiKey.is_active == True,
            )
            .options(
                # Load role eagerly to avoid lazy loading issues in async context if needed,
                # though this is sync repo.
                # Actually, `selectinload` is good practice.
                selectinload(RoleApiKey.role)
            )
        )
        return list(self.session.exec(statement).all())
