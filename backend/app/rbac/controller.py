from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, status

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import RolePermission as CoreRolePermission
from app.rbac.application.dtos import (
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleApiKeyCreate,
    RoleApiKeyResponse,
    RoleApiKeySecret,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)
from app.rbac.application.use_cases import RoleApiKeyUseCases, RoleUseCases
from app.shared.application.response import ApiResponse

# Combined router — prefix khớp frontend: /api/v1/rbac/...
router = APIRouter(prefix="/rbac", tags=["rbac"])


# --- Role Endpoints ---
@router.get("/roles", response_model=ApiResponse[list[RoleResponse]])
@inject
async def get_roles(
    use_cases: FromDishka[RoleUseCases],
    _current_user: CurrentUser,
):
    """Retrieve all roles (accessible by all authenticated users)"""
    roles = use_cases.get_all_roles()
    return ApiResponse.success(data=roles, message="Roles retrieved successfully")


@router.post(
    "/roles",
    response_model=ApiResponse[RoleResponse],
    dependencies=[hasPermission(CoreRolePermission.CREATE)],
)
@inject
async def create_role(
    role_data: RoleCreate,
    use_cases: FromDishka[RoleUseCases],
):
    """Create a new role (Admin only)"""
    role = use_cases.create_role(role_data)
    return ApiResponse.created(data=role, message="Role created successfully")


@router.put(
    "/roles/{role_id}",
    response_model=ApiResponse[RoleResponse],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
@inject
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    use_cases: FromDishka[RoleUseCases],
):
    """Update a role (Admin only)"""
    role = use_cases.update_role(role_id, role_data)
    if not role:
        return ApiResponse.error(message="Role not found")
    return ApiResponse.success(data=role, message="Role updated successfully")


@router.delete(
    "/roles/{role_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.DELETE)],
)
@inject
async def delete_role(
    role_id: int,
    use_cases: FromDishka[RoleUseCases],
):
    """Delete a role (Admin only)"""
    success = use_cases.delete_role(role_id)
    if not success:
        return ApiResponse.error(message="Role not found")
    return ApiResponse.success(message="Role deleted successfully")


# --- Permission Endpoints ---
@router.get("/permissions", response_model=ApiResponse[list[PermissionResponse]])
@inject
async def get_permissions(
    use_cases: FromDishka[RoleUseCases],
    _current_user: CurrentUser,
):
    """Retrieve all permissions (accessible by all authenticated users)"""
    perms = use_cases.get_all_permissions()
    return ApiResponse.success(data=perms, message="Permissions retrieved successfully")


@router.post(
    "/permissions",
    response_model=ApiResponse[PermissionResponse],
    dependencies=[hasPermission(CoreRolePermission.CREATE)],
)
@inject
async def create_permission(
    perm_data: PermissionCreate,
    use_cases: FromDishka[RoleUseCases],
):
    """Create a new permission (Admin only)"""
    perm = use_cases.create_permission(perm_data)
    return ApiResponse.created(data=perm, message="Permission created successfully")


@router.put(
    "/permissions/{perm_id}",
    response_model=ApiResponse[PermissionResponse],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
@inject
async def update_permission(
    perm_id: int,
    perm_data: PermissionUpdate,
    use_cases: FromDishka[RoleUseCases],
):
    """Update a permission (Admin only)"""
    perm = use_cases.update_permission(perm_id, perm_data)
    if not perm:
        return ApiResponse.error(message="Permission not found")
    return ApiResponse.success(data=perm, message="Permission updated successfully")


@router.delete(
    "/permissions/{perm_id}",
    response_model=ApiResponse[None],
    dependencies=[
        hasPermission(CoreRolePermission.UPDATE)
    ],  # Note: Keeping the original decorator requirement
)
@inject
async def delete_permission(
    perm_id: int,
    use_cases: FromDishka[RoleUseCases],
):
    """Delete a permission (Admin only)"""
    success = use_cases.delete_permission(perm_id)
    if not success:
        return ApiResponse.error(message="Permission not found")
    return ApiResponse.success(message="Permission deleted successfully")


# --- Role-Permission Link Endpoints ---
@router.post(
    "/roles/{role_id}/permissions/{perm_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
@inject
async def add_permission_to_role(
    role_id: int,
    perm_id: int,
    use_cases: FromDishka[RoleUseCases],
):
    """Assign a permission to a role (Admin only)"""
    success, message = use_cases.add_permission_to_role(role_id, perm_id)
    if not success:
        return ApiResponse.error(
            message=message, status_code=status.HTTP_400_BAD_REQUEST
        )
    return ApiResponse.success(message=message)


@router.delete(
    "/roles/{role_id}/permissions/{perm_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
@inject
async def remove_permission_from_role(
    role_id: int,
    perm_id: int,
    use_cases: FromDishka[RoleUseCases],
):
    """Remove a permission from a role (Admin only)"""
    success, message = use_cases.remove_permission_from_role(role_id, perm_id)
    if not success:
        return ApiResponse.error(
            message=message, status_code=status.HTTP_400_BAD_REQUEST
        )
    return ApiResponse.success(message=message)


# --- API Key Endpoints ---
@router.post(
    "/api-keys",
    response_model=ApiResponse[RoleApiKeySecret],
    dependencies=[hasPermission(CoreRolePermission.CREATE)],
)
@inject
async def create_api_key(
    data: RoleApiKeyCreate,
    use_cases: FromDishka[RoleApiKeyUseCases],
):
    """Create a new API Key for a Role (Admin only)"""
    result, message = use_cases.create_api_key(data)
    if not result:
        return ApiResponse.error(
            message=message, status_code=status.HTTP_400_BAD_REQUEST
        )

    return ApiResponse.created(data=result, message="API Key created successfully")


@router.get(
    "/api-keys/role/{role_id}",
    response_model=ApiResponse[list[RoleApiKeyResponse]],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
@inject
async def get_role_api_keys(
    role_id: int,
    use_cases: FromDishka[RoleApiKeyUseCases],
):
    """Get all API Keys for a specific Role (Admin only)"""
    keys = use_cases.get_by_role(role_id)
    return ApiResponse.success(data=keys, message="API Keys retrieved successfully")


@router.delete(
    "/api-keys/{key_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.DELETE)],
)
@inject
async def revoke_api_key(
    key_id: int,
    use_cases: FromDishka[RoleApiKeyUseCases],
):
    """Revoke (delete) an API Key"""
    success, message = use_cases.revoke_api_key(key_id)
    if not success:
        return ApiResponse.error(message=message)
    return ApiResponse.success(message=message)
