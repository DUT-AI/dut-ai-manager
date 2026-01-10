from typing import Annotated, List

from app.core.deps import ServiceFactoryDI, hasPermission
from app.core.permissions import UserPermission
from app.models import User
from app.schemas.response import ApiResponse
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "",
    response_model=ApiResponse[List[UserResponse]],
    dependencies=[hasPermission(UserPermission.READ)],
)
async def get_users(
    service_factory: ServiceFactoryDI,
):
    """Retrieve all users"""
    users = service_factory.user.get_all_users()
    return ApiResponse.success(data=[UserResponse.model_validate(u) for u in users])


@router.get(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    dependencies=[hasPermission(UserPermission.READ)],
)
async def get_user(
    user_id: int,
    service_factory: ServiceFactoryDI,
):
    """Get a specific user by ID"""
    user = service_factory.user.get_user_by_id(user_id)
    return ApiResponse.success(data=UserResponse.model_validate(user))


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
    dependencies=[hasPermission(UserPermission.CREATE)],
)
async def create_user(
    user_data: UserCreate,
    service_factory: ServiceFactoryDI,
):
    """Create a new user"""
    success, user, message = service_factory.user.create_user(user_data)
    if not success:
        return ApiResponse.error(message=message, status_code=400)
    return ApiResponse.success(
        data=UserResponse.model_validate(user), message=message, status_code=201
    )


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    _user: Annotated[User, hasPermission(UserPermission.UPDATE)],
    service_factory: ServiceFactoryDI,
):
    """Update a user"""
    user = service_factory.user.update_user(user_id, user_data)
    return ApiResponse.success(data=UserResponse.model_validate(user))


@router.delete("/{user_id}", response_model=ApiResponse[None])
async def delete_user(
    user_id: int,
    _user: Annotated[User, hasPermission(UserPermission.DELETE)],
    service_factory: ServiceFactoryDI,
):
    """Delete a user"""
    success = service_factory.user.delete_user(user_id)
    if not success:
        return ApiResponse.error(message="User not found", status_code=404)
    return ApiResponse.success(message="User deleted successfully")
