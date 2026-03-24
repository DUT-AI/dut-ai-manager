from typing import Annotated, List

from app.core.deps import CurrentUser, hasPermission, ServiceFactoryDI
from app.core.permissions import RolePermission
from app.models import User
from app.schemas.response import ApiResponse
from app.schemas.role_api_key import (
    RoleApiKeyCreate,
    RoleApiKeyResponse,
    RoleApiKeySecret,
)
from fastapi import APIRouter, status   

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.post("", response_model=ApiResponse[RoleApiKeySecret])
async def create_api_key(
    _user: Annotated[User, hasPermission(RolePermission.CREATE)],
    data: RoleApiKeyCreate,
    service_factory: ServiceFactoryDI,
):
    """Create a new API Key for a Role (Admin only)"""
    result, message = service_factory.role_api_key.create_api_key(data)
    if not result:
        return ApiResponse.error(
            message=message, status_code=status.HTTP_400_BAD_REQUEST
        )

    return ApiResponse.created(data=result, message="API Key created successfully")


@router.get("/role/{role_id}", response_model=ApiResponse[List[RoleApiKeyResponse]])
async def get_role_api_keys(
    _user: Annotated[User, hasPermission(RolePermission.UPDATE)],
    role_id: int,
    service_factory: ServiceFactoryDI,
):
    """Get all API Keys for a specific Role (Admin only)"""
    keys = service_factory.role_api_key.get_by_role(role_id)
    return ApiResponse.success(data=keys, message="API Keys retrieved successfully")


@router.delete("/{key_id}", response_model=ApiResponse[None])
async def revoke_api_key(
    _user: Annotated[User, hasPermission(RolePermission.DELETE)],
    key_id: int,
    service_factory: ServiceFactoryDI,
):
    """Revoke (delete) an API Key"""
    success, message = service_factory.role_api_key.revoke_api_key(key_id)
    if not success:
        return ApiResponse.not_found(message=message)
    return ApiResponse.success(message=message)
