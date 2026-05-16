from datetime import datetime

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


class PermissionBase(BaseModel):
    name: str
    description: str | None = None
    resource: str
    action: str


class PermissionCreate(PermissionBase):
    pass


class PermissionUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    resource: str | None = None
    action: str | None = None


class PermissionResponse(PermissionBase):
    id: int

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str
    description: str | None = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class RoleResponse(RoleBase):
    id: int
    permissions: list[PermissionResponse] = []

    class Config:
        from_attributes = True


class RolePermissionLink(BaseModel):
    role_id: int
    permission_id: int
