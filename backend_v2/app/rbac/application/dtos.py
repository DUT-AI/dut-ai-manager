from pydantic import BaseModel, ConfigDict, Field


# --- Permission DTOs ---
class PermissionCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(default=None, max_length=255)
    resource: str = Field(..., max_length=100)
    action: str = Field(..., max_length=50)


class PermissionUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    resource: str | None = Field(default=None, max_length=100)
    action: str | None = Field(default=None, max_length=50)


class PermissionResponse(BaseModel):
    id: int
    name: str
    description: str | None
    resource: str
    action: str

    model_config = ConfigDict(from_attributes=True)


# --- Role DTOs ---
class RoleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleResponse(BaseModel):
    id: int
    name: str
    description: str | None
    permissions: list[PermissionResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Role API Key DTOs ---
class RoleApiKeyCreate(BaseModel):
    name: str = Field(..., max_length=255)


class RoleApiKeyResponse(BaseModel):
    id: int
    name: str
    prefix: str
    is_active: bool
    role_id: int

    model_config = ConfigDict(from_attributes=True)


class RoleApiKeySecret(RoleApiKeyResponse):
    key: str  # The raw API key (only returned once upon creation)
