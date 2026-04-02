from typing import Annotated, List

from app.core.deps import CurrentUser, hasPermission
from app.core.permissions import RolePermission as CoreRolePermission
from app.rbac.deps import RoleApiKeyUseCasesDI, RoleUseCasesDI
from app.shared.application.response import ApiResponse
from app.rbac.application.dtos import (
    RoleApiKeyCreate,
    RoleApiKeyResponse,
    RoleApiKeySecret,
    PermissionCreate,
    PermissionResponse,
    PermissionUpdate,
    RoleCreate,
    RoleResponse,
    RoleUpdate,
)

from fastapi import APIRouter, status

# Combined router — prefix khớp frontend: /api/v1/rbac/...
router = APIRouter(prefix="/rbac", tags=["rbac"])


# --- Role Endpoints ---
@router.get("/roles", response_model=ApiResponse[List[RoleResponse]])
async def get_roles(
    current_user: CurrentUser,
    use_cases: RoleUseCasesDI,
):
    """Retrieve all roles (accessible by all authenticated users)"""
    roles = use_cases.get_all_roles()
    return ApiResponse.success(data=roles, message="Roles retrieved successfully")


@router.post(
    "/roles",
    response_model=ApiResponse[RoleResponse],
    dependencies=[hasPermission(CoreRolePermission.CREATE)],
)
async def create_role(
    role_data: RoleCreate,
    use_cases: RoleUseCasesDI,
):
    """Create a new role (Admin only)"""
    role = use_cases.create_role(role_data)
    return ApiResponse.created(data=role, message="Role created successfully")


@router.put(
    "/roles/{role_id}",
    response_model=ApiResponse[RoleResponse],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    use_cases: RoleUseCasesDI,
):
    """Update a role (Admin only)"""
    role = use_cases.update_role(role_id, role_data)
    if not role:
        return ApiResponse.not_found(message="Role not found")
    return ApiResponse.success(data=role, message="Role updated successfully")


@router.delete(
    "/roles/{role_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.DELETE)],
)
async def delete_role(
    role_id: int,
    use_cases: RoleUseCasesDI,
):
    """Delete a role (Admin only)"""
    success = use_cases.delete_role(role_id)
    if not success:
        return ApiResponse.not_found(message="Role not found")
    return ApiResponse.success(message="Role deleted successfully")


# --- Permission Endpoints ---
@router.get("/permissions", response_model=ApiResponse[List[PermissionResponse]])
async def get_permissions(
    current_user: CurrentUser,
    use_cases: RoleUseCasesDI,
):
    """Retrieve all permissions (accessible by all authenticated users)"""
    perms = use_cases.get_all_permissions()
    return ApiResponse.success(data=perms, message="Permissions retrieved successfully")


@router.post(
    "/permissions",
    response_model=ApiResponse[PermissionResponse],
    dependencies=[hasPermission(CoreRolePermission.CREATE)],
)
async def create_permission(
    perm_data: PermissionCreate,
    use_cases: RoleUseCasesDI,
):
    """Create a new permission (Admin only)"""
    perm = use_cases.create_permission(perm_data)
    return ApiResponse.created(data=perm, message="Permission created successfully")


@router.put(
    "/permissions/{perm_id}",
    response_model=ApiResponse[PermissionResponse],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
async def update_permission(
    perm_id: int,
    perm_data: PermissionUpdate,
    use_cases: RoleUseCasesDI,
):
    """Update a permission (Admin only)"""
    perm = use_cases.update_permission(perm_id, perm_data)
    if not perm:
        return ApiResponse.not_found(message="Permission not found")
    return ApiResponse.success(data=perm, message="Permission updated successfully")


@router.delete(
    "/permissions/{perm_id}",
    response_model=ApiResponse[None],
    dependencies=[
        hasPermission(CoreRolePermission.UPDATE)
    ],  # Note: Keeping the original decorator requirement
)
async def delete_permission(
    perm_id: int,
    use_cases: RoleUseCasesDI,
):
    """Delete a permission (Admin only)"""
    success = use_cases.delete_permission(perm_id)
    if not success:
        return ApiResponse.not_found(message="Permission not found")
    return ApiResponse.success(message="Permission deleted successfully")


# --- Role-Permission Link Endpoints ---
@router.post(
    "/roles/{role_id}/permissions/{perm_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
async def add_permission_to_role(
    role_id: int,
    perm_id: int,
    use_cases: RoleUseCasesDI,
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
async def remove_permission_from_role(
    role_id: int,
    perm_id: int,
    use_cases: RoleUseCasesDI,
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
async def create_api_key(
    data: RoleApiKeyCreate,
    use_cases: RoleApiKeyUseCasesDI,
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
    response_model=ApiResponse[List[RoleApiKeyResponse]],
    dependencies=[hasPermission(CoreRolePermission.UPDATE)],
)
async def get_role_api_keys(
    role_id: int,
    use_cases: RoleApiKeyUseCasesDI,
):
    """Get all API Keys for a specific Role (Admin only)"""
    keys = use_cases.get_by_role(role_id)
    return ApiResponse.success(data=keys, message="API Keys retrieved successfully")


@router.delete(
    "/api-keys/{key_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(CoreRolePermission.DELETE)],
)
async def revoke_api_key(
    key_id: int,
    use_cases: RoleApiKeyUseCasesDI,
):
    """Revoke (delete) an API Key"""
    success, message = use_cases.revoke_api_key(key_id)
    if not success:
        return ApiResponse.not_found(message=message)
    return ApiResponse.success(message=message)
