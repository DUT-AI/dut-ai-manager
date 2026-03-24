from app.shared.base_exception import DomainException


class RoleNotFoundException(DomainException):
    def __init__(self, role_id: int | str):
        super().__init__(f"Role with identifier {role_id} not found", status_code=404)


class RoleAlreadyExistsException(DomainException):
    def __init__(self, name: str):
        super().__init__(f"Role with name '{name}' already exists", status_code=400)


class PermissionNotFoundException(DomainException):
    def __init__(self, permission_id: int | str):
        super().__init__(
            f"Permission with identifier {permission_id} not found", status_code=404
        )


class PermissionAlreadyExistsException(DomainException):
    def __init__(self, name: str):
        super().__init__(
            f"Permission with name '{name}' already exists", status_code=400
        )


class RoleApiKeyNotFoundException(DomainException):
    def __init__(self, key_id: int):
        super().__init__(f"Role API Key with ID {key_id} not found", status_code=404)


class PermissionAlreadyAssignedException(DomainException):
    def __init__(self, role_id: int, permission_id: int):
        super().__init__(
            f"Permission {permission_id} is already assigned to Role {role_id}",
            status_code=400,
        )


class PermissionNotAssignedException(DomainException):
    def __init__(self, role_id: int, permission_id: int):
        super().__init__(
            f"Permission {permission_id} is not assigned to Role {role_id}",
            status_code=400,
        )
