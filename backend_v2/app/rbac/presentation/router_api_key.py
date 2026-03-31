from app.rbac.application.dtos import (RoleApiKeyCreate, RoleApiKeyResponse,
                                       RoleApiKeySecret)
from app.rbac.application.use_cases.create_role_api_key import \
  CreateRoleApiKeyUseCase
from app.rbac.application.use_cases.manage_role_api_key import (
  GetRoleApiKeysUseCase, RevokeRoleApiKeyUseCase)
from app.shared.api_response import ApiResponse
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiResponse[RoleApiKeySecret])
@inject
async def create_api_key(
    data: RoleApiKeyCreate,
    role_id: int,  # Assuming role_id is passed as a query param or you can move it to the DTO
    use_case: FromDishka[CreateRoleApiKeyUseCase],
    # _user: Annotated[User, hasPermission(RolePermission.CREATE)], # Skipped for now
):
    """Create a new API Key for a Role."""
    result = await use_case.execute(role_id=role_id, dto=data)
    return ApiResponse.created(data=result, message="API Key created successfully")


@router.get("/role/{role_id}", response_model=ApiResponse[list[RoleApiKeyResponse]])
@inject
async def get_role_api_keys(
    role_id: int,
    use_case: FromDishka[GetRoleApiKeysUseCase],
):
    """Get all API Keys for a specific Role."""
    keys = await use_case.execute(role_id=role_id)
    return ApiResponse.success(data=keys, message="API Keys retrieved successfully")


@router.delete("/{key_id}", response_model=ApiResponse[None])
@inject
async def revoke_api_key(
    key_id: int,
    use_case: FromDishka[RevokeRoleApiKeyUseCase],
):
    """Revoke (delete) an API Key."""
    await use_case.execute(key_id=key_id)
    return ApiResponse.success(message="API Key deleted/revoked successfully")
