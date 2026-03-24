from enum import Enum


class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class UserPermission(str, Enum):
    CREATE = "user:create"
    READ = "user:read"
    UPDATE = "user:update"
    DELETE = "user:delete"


class AccountPermission(str, Enum):
    CREATE = "account:create"
    READ = "account:read"
    UPDATE = "account:update"
    DELETE = "account:delete"
