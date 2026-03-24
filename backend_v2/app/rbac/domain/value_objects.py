from enum import Enum


class RolePermission(str, Enum):
    CREATE = "role:create"
    READ = "role:read"
    UPDATE = "role:update"
    DELETE = "role:delete"


class PermissionPermission(str, Enum):
    CREATE = "permission:create"
    READ = "permission:read"
    UPDATE = "permission:update"
    DELETE = "permission:delete"


class RoleApiKeyPermission(str, Enum):
    CREATE = "api_key:create"
    READ = "api_key:read"
    UPDATE = "api_key:update"
    DELETE = "api_key:delete"
