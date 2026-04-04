from enum import Enum


class AccountPermission(str, Enum):
    CREATE = "account:create"
    READ = "account:read"
    UPDATE = "account:update"
    DELETE = "account:delete"


class RolePermission(str, Enum):
    CREATE = "role:create"
    READ = "role:read"
    UPDATE = "role:update"
    DELETE = "role:delete"


class UserPermission(str, Enum):
    CREATE = "user:create"
    READ = "user:read"
    UPDATE = "user:update"
    DELETE = "user:delete"


class BonusPointPermission(str, Enum):
    CREATE = "bonus_point:create"
    READ = "bonus_point:read"
    UPDATE = "bonus_point:update"
    DELETE = "bonus_point:delete"


class ViolationPermission(str, Enum):
    CREATE = "violation:create"
    READ = "violation:read"
    UPDATE = "violation:update"
    DELETE = "violation:delete"


class PermissionRequestPermission(str, Enum):
    CREATE = "permission_request:create"
    READ = "permission_request:read"
    UPDATE = "permission_request:update"
    DELETE = "permission_request:delete"


class PermissionPermission(str, Enum):
    CREATE = "permission:create"
    READ = "permission:read"
    UPDATE = "permission:update"
    DELETE = "permission:delete"


class TeamPermission(str, Enum):
    CREATE = "team:create"
    READ = "team:read"
    UPDATE = "team:update"
    DELETE = "team:delete"


class TeamMemberPermission(str, Enum):
    CREATE = "team_member:create"
    READ = "team_member:read"
    UPDATE = "team_member:update"
    DELETE = "team_member:delete"


class HomeworkPermission(str, Enum):
    CREATE = "homework:create"
    READ = "homework:read"
    UPDATE = "homework:update"
    DELETE = "homework:delete"


class HomeworkSubmissionPermission(str, Enum):
    CREATE = "homework_submission:create"
    READ = "homework_submission:read"
    UPDATE = "homework_submission:update"
    DELETE = "homework_submission:delete"


class MeetingPermission(str, Enum):
    CREATE = "meeting:create"
    READ = "meeting:read"
    UPDATE = "meeting:update"
    DELETE = "meeting:delete"


class BillingPermission(str, Enum):
    CREATE = "billing:create"
    READ = "billing:read"
    UPDATE = "billing:update"
    DELETE = "billing:delete"
    MY_INVOICES = "billing:my_invoices"
