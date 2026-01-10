from typing import Annotated, List

from app.core.deps import CurrentUser, hasPermission, ServiceFactoryDI
from app.core.permissions import RolePermission
from app.models import User
from app.schemas.response import ApiResponse
from app.schemas.role_permission import (
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    PermissionCreate,
    PermissionUpdate,
    PermissionResponse,
)
from fastapi import APIRouter, status

router = APIRouter(prefix="/rbac", tags=["rbac"])


# --- Role Endpoints ---
@router.get("/roles", response_model=ApiResponse[List[RoleResponse]])
async def get_roles(
    current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
):
    """Retrieve all roles (accessible by all authenticated users)"""
    roles = service_factory.role_permission.get_all_roles()
    return ApiResponse.success(data=roles, message="Roles retrieved successfully")


@router.post("/roles", response_model=ApiResponse[RoleResponse])
async def create_role(
    _user: Annotated[User, hasPermission(RolePermission.CREATE)],
    role_data: RoleCreate,
    service_factory: ServiceFactoryDI,
):
    """Create a new role (Admin only)"""
    role = service_factory.role_permission.create_role(role_data)
    return ApiResponse.created(data=role, message="Role created successfully")


@router.put("/roles/{role_id}", response_model=ApiResponse[RoleResponse])
async def update_role(
    _user: Annotated[User, hasPermission(RolePermission.UPDATE)],
    role_id: int,
    role_data: RoleUpdate,
    service_factory: ServiceFactoryDI,
):
    """Update a role (Admin only)"""
    role = service_factory.role_permission.update_role(role_id, role_data)
    if not role:
        return ApiResponse.not_found(message="Role not found")
    return ApiResponse.success(data=role, message="Role updated successfully")


@router.delete("/roles/{role_id}", response_model=ApiResponse[None])
async def delete_role(
    _user: Annotated[User, hasPermission(RolePermission.DELETE)],
    role_id: int,
    service_factory: ServiceFactoryDI,
):
    """Delete a role (Admin only)"""
    success = service_factory.role_permission.delete_role(role_id)
    if not success:
        return ApiResponse.not_found(message="Role not found")
    return ApiResponse.success(message="Role deleted successfully")


# --- Permission Endpoints ---
@router.get("/permissions", response_model=ApiResponse[List[PermissionResponse]])
async def get_permissions(
    current_user: CurrentUser,
    service_factory: ServiceFactoryDI,
):
    """Retrieve all permissions (accessible by all authenticated users)"""
    perms = service_factory.role_permission.get_all_permissions()
    return ApiResponse.success(data=perms, message="Permissions retrieved successfully")


@router.post("/permissions", response_model=ApiResponse[PermissionResponse])
async def create_permission(
    _user: Annotated[User, hasPermission(RolePermission.CREATE)],
    perm_data: PermissionCreate,
    service_factory: ServiceFactoryDI,
):
    """Create a new permission (Admin only)"""
    perm = service_factory.role_permission.create_permission(perm_data)
    return ApiResponse.created(data=perm, message="Permission created successfully")


@router.put("/permissions/{perm_id}", response_model=ApiResponse[PermissionResponse])
async def update_permission(
    _user: Annotated[User, hasPermission(RolePermission.UPDATE)],
    perm_id: int,
    perm_data: PermissionUpdate,
    service_factory: ServiceFactoryDI,
):
    """Update a permission (Admin only)"""
    perm = service_factory.role_permission.update_permission(perm_id, perm_data)
    if not perm:
        return ApiResponse.not_found(message="Permission not found")
    return ApiResponse.success(data=perm, message="Permission updated successfully")


@router.delete("/permissions/{perm_id}", response_model=ApiResponse[None])
async def delete_permission(
    _user: Annotated[User, hasPermission(RolePermission.UPDATE)],
    perm_id: int,
    service_factory: ServiceFactoryDI,
):
    """Delete a permission (Admin only)"""
    success = service_factory.role_permission.delete_permission(perm_id)
    if not success:
        return ApiResponse.not_found(message="Permission not found")
    return ApiResponse.success(message="Permission deleted successfully")


# --- Role-Permission Link Endpoints ---
@router.post("/roles/{role_id}/permissions/{perm_id}", response_model=ApiResponse[None])
async def add_permission_to_role(
    _user: Annotated[User, hasPermission(RolePermission.UPDATE)],
    role_id: int,
    perm_id: int,
    service_factory: ServiceFactoryDI,
):
    """Assign a permission to a role (Admin only)"""
    success, message = service_factory.role_permission.add_permission_to_role(
        role_id, perm_id
    )
    if not success:
        return ApiResponse.error(
            message=message, status_code=status.HTTP_400_BAD_REQUEST
        )
    return ApiResponse.success(message=message)


@router.delete(
    "/roles/{role_id}/permissions/{perm_id}", response_model=ApiResponse[None]
)
async def remove_permission_from_role(
    _user: Annotated[User, hasPermission(RolePermission.UPDATE)],
    role_id: int,
    perm_id: int,
    service_factory: ServiceFactoryDI,
):
    """Remove a permission from a role (Admin only)"""
    success, message = service_factory.role_permission.remove_permission_from_role(
        role_id, perm_id
    )
    if not success:
        return ApiResponse.error(
            message=message, status_code=status.HTTP_400_BAD_REQUEST
        )
    return ApiResponse.success(message=message)
