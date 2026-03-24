from app.rbac.application.dtos import (PermissionCreate, PermissionResponse,
                                       RoleCreate, RoleResponse, RoleUpdate)
from app.rbac.application.use_cases.get_roles import GetRolesUseCase
# Missing imports for other use cases would go here,
# for brevity we'll just import the ones we wrote completely.
from app.rbac.application.use_cases.manage_permission import (
  CreatePermissionUseCase, DeletePermissionUseCase, GetPermissionsUseCase)
from app.rbac.application.use_cases.manage_role import (CreateRoleUseCase,
                                                        DeleteRoleUseCase,
                                                        UpdateRoleUseCase)
from app.rbac.application.use_cases.manage_role_permission import (
  AssignPermissionToRoleUseCase, RemovePermissionFromRoleUseCase)
from app.shared.api_response import ApiResponse
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

router = APIRouter(prefix="/rbac", tags=["rbac"])


# --- ROLES ---
@router.get("/roles", response_model=ApiResponse[list[RoleResponse]])
@inject
async def get_roles(
    use_case: FromDishka[GetRolesUseCase],
):
    roles = await use_case.execute()
    return ApiResponse.success(data=roles, message="Roles retrieved successfully")


@router.post("/roles", response_model=ApiResponse[RoleResponse])
@inject
async def create_role(
    data: RoleCreate,
    use_case: FromDishka[CreateRoleUseCase],
):
    role = await use_case.execute(dto=data)
    return ApiResponse.created(data=role, message="Role created successfully")


@router.put("/roles/{role_id}", response_model=ApiResponse[RoleResponse])
@inject
async def update_role(
    role_id: int,
    data: RoleUpdate,
    use_case: FromDishka[UpdateRoleUseCase],
):
    role = await use_case.execute(role_id=role_id, dto=data)
    return ApiResponse.success(data=role, message="Role updated successfully")


@router.delete("/roles/{role_id}", response_model=ApiResponse[None])
@inject
async def delete_role(
    role_id: int,
    use_case: FromDishka[DeleteRoleUseCase],
):
    await use_case.execute(role_id=role_id)
    return ApiResponse.success(message="Role deleted successfully")


# --- PERMISSIONS ---
@router.get("/permissions", response_model=ApiResponse[list[PermissionResponse]])
@inject
async def get_permissions(
    use_case: FromDishka[GetPermissionsUseCase],
):
    perms = await use_case.execute()
    return ApiResponse.success(data=perms, message="Permissions retrieved successfully")


@router.post("/permissions", response_model=ApiResponse[PermissionResponse])
@inject
async def create_permission(
    data: PermissionCreate,
    use_case: FromDishka[CreatePermissionUseCase],
):
    perm = await use_case.execute(dto=data)
    return ApiResponse.created(data=perm, message="Permission created successfully")


@router.delete("/permissions/{perm_id}", response_model=ApiResponse[None])
@inject
async def delete_permission(
    perm_id: int,
    use_case: FromDishka[DeletePermissionUseCase],
):
    await use_case.execute(permission_id=perm_id)
    return ApiResponse.success(message="Permission deleted successfully")


# --- ROLE-PERMISSION LINKS ---
@router.post("/roles/{role_id}/permissions/{perm_id}", response_model=ApiResponse[None])
@inject
async def add_permission_to_role(
    role_id: int,
    perm_id: int,
    use_case: FromDishka[AssignPermissionToRoleUseCase],
):
    await use_case.execute(role_id=role_id, permission_id=perm_id)
    return ApiResponse.success(message="Permission assigned successfully")


@router.delete(
    "/roles/{role_id}/permissions/{perm_id}", response_model=ApiResponse[None]
)
@inject
async def remove_permission_from_role(
    role_id: int,
    perm_id: int,
    use_case: FromDishka[RemovePermissionFromRoleUseCase],
):
    await use_case.execute(role_id=role_id, permission_id=perm_id)
    return ApiResponse.success(message="Permission removed successfully")
