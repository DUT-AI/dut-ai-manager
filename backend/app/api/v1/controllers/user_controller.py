from typing import List

from app.core.deps import (
    ServiceFactoryDI,
    hasPermission,
    CurrentUser,
    onlyEditOrDeleteYourself,
)
from app.core.permissions import UserPermission
from app.schemas.response import ApiResponse
from app.schemas.user import (
    UserCreate,
    UserResponse,
    UserUpdate,
    UserSettingsUpdate,
    UserImportResult,
)
from fastapi import APIRouter, UploadFile, BackgroundTasks

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
    background_tasks: BackgroundTasks,
):
    """Create a new user"""
    user = service_factory.user.create_user(user_data, background_tasks)
    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="User created successfully",
        status_code=201,
    )


@router.post(
    "/import",
    response_model=ApiResponse[UserImportResult],
    dependencies=[hasPermission(UserPermission.CREATE)],
)
async def import_users(
    file: UploadFile,
    service_factory: ServiceFactoryDI,
    background_tasks: BackgroundTasks,
):
    """Import users from Excel file"""
    result = await service_factory.user.import_users(file, background_tasks)
    return ApiResponse.success(data=result, message="User import processed")


@router.put(
    "/me/settings",
    response_model=ApiResponse[UserResponse],
)
async def update_me(
    settings_data: UserSettingsUpdate,
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
):
    """Update current user's settings (avatar and discord_id)"""
    user = service_factory.user.update_settings(current_user.id, settings_data)
    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="Settings updated successfully",
        status_code=200,
    )


@router.post(
    "/me/avatar",
    response_model=ApiResponse[UserResponse],
)
async def update_avatar_me(
    file: UploadFile,
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
):
    """Upload avatar for current user"""
    user = await service_factory.user.update_avatar(current_user.id, file)
    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="Avatar uploaded successfully",
        status_code=200,
    )


@router.put(
    "/{user_id}",
    response_model=ApiResponse[UserResponse],
    dependencies=[
        hasPermission(UserPermission.UPDATE),
        onlyEditOrDeleteYourself("user_id"),
    ],
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    service_factory: ServiceFactoryDI,
    current_user: CurrentUser,
):
    """Update a user"""
    user = service_factory.user.update_user(user_id, user_data, current_user)
    return ApiResponse.success(
        data=UserResponse.model_validate(user),
        message="User updated successfully",
        status_code=200,
    )


@router.delete(
    "/{user_id}",
    response_model=ApiResponse[None],
    dependencies=[hasPermission(UserPermission.DELETE)],
)
async def delete_user(
    user_id: int,
    service_factory: ServiceFactoryDI,
):
    """Delete a user"""
    service_factory.user.delete_user(user_id)
    return ApiResponse.success(message="User deleted successfully")
