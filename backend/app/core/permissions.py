from enum import StrEnum


class AccountPermission(StrEnum):
    CREATE = "account:create"
    READ = "account:read"
    UPDATE = "account:update"
    DELETE = "account:delete"


class RolePermission(StrEnum):
    CREATE = "role:create"
    READ = "role:read"
    UPDATE = "role:update"
    DELETE = "role:delete"


class UserPermission(StrEnum):
    CREATE = "user:create"
    READ = "user:read"
    UPDATE = "user:update"
    DELETE = "user:delete"


class BonusPointPermission(StrEnum):
    CREATE = "bonus_point:create"
    READ = "bonus_point:read"
    UPDATE = "bonus_point:update"
    DELETE = "bonus_point:delete"


class ViolationPermission(StrEnum):
    CREATE = "violation:create"
    READ = "violation:read"
    UPDATE = "violation:update"
    DELETE = "violation:delete"


class PermissionRequestPermission(StrEnum):
    CREATE = "permission_request:create"
    READ = "permission_request:read"
    UPDATE = "permission_request:update"
    DELETE = "permission_request:delete"


class PermissionPermission(StrEnum):
    CREATE = "permission:create"
    READ = "permission:read"
    UPDATE = "permission:update"
    DELETE = "permission:delete"


class TeamPermission(StrEnum):
    CREATE = "team:create"
    READ = "team:read"
    UPDATE = "team:update"
    DELETE = "team:delete"


class TeamMemberPermission(StrEnum):
    CREATE = "team_member:create"
    READ = "team_member:read"
    UPDATE = "team_member:update"
    DELETE = "team_member:delete"


class HomeworkPermission(StrEnum):
    CREATE = "homework:create"
    READ = "homework:read"
    UPDATE = "homework:update"
    DELETE = "homework:delete"


class MeetingPermission(StrEnum):
    CREATE = "meeting:create"
    READ = "meeting:read"
    UPDATE = "meeting:update"
    DELETE = "meeting:delete"
    CHECK_IN = "meeting:check_in"


class BillingPermission(StrEnum):
    CREATE = "billing:create"
    READ = "billing:read"
    UPDATE = "billing:update"
    DELETE = "billing:delete"
    MY_INVOICES = "billing:my_invoices"


class ExpensePermission(StrEnum):
    CREATE = "expense:create"
    READ = "expense:read"
    UPDATE = "expense:update"
    DELETE = "expense:delete"


class DutyPermission(StrEnum):
    CREATE = "duty:create"
    READ = "duty:read"
    UPDATE = "duty:update"
    DELETE = "duty:delete"
    SUBMIT = "duty:submit"
