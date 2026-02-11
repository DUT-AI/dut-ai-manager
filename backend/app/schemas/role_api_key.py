from datetime import datetime
from typing import Optional

from app.schemas.role_permission import RoleBase
from pydantic import BaseModel


class RoleApiKeyCreate(BaseModel):
    name: str
    role_id: int


class RoleApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    created_at: datetime
    role_id: int

    class Config:
        from_attributes = True


# Special schema that returns the full secret key ONLY once upon creation
class RoleApiKeySecret(RoleApiKeyResponse):
    secret_key: str
