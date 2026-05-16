"""
User Web Controller — provides API routes.
"""

from typing import Annotated

from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile

from app.core.deps import CurrentUser, PermissionChecker
from app.core.permissions import UserPermission
from app.shared.application.response import ApiResponse
from app.user.application.dtos import (
    UserCreate,
    UserImportResult,
    UserResponse,
    UserSettingsUpdate,
    UserUpdate,
)
from app.user.application.use_cases import (
    CreateUserUseCase,
    DeleteUserUseCase,
    GetUserUseCase,
    ImportUsersUseCase,
    UpdateAvatarUseCase,
    UpdateUserUseCase,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse[list[UserResponse]])
@inject
async def list_users(
    _: Annotated[CurrentUser, Depends(PermissionChecker(UserPermission.READ))],
    uc: FromDishka[GetUserUseCase],
    keyword: str | None = Query(None, description="Search by name or email"),
):
    """List all users or search by keyword."""
    if keyword:
        users = uc.search(keyword)
    else:
        users = uc.get_all()

    return ApiResponse.success(
        data=[UserResponse.model_validate(u) for u in users],
        message="Fetched users successfully",
    )


@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
@inject
async def get_user_by_id(
    user_id: int,
    uc: FromDishka[GetUserUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(UserPermission.READ))],
):
    """Retrieve a specific user by ID."""
    user = uc.execute(user_id)
    return ApiResponse.success(
        data=UserResponse.model_validate(user), message="Fetched user profile"
    )


@router.post(
    "",
    response_model=ApiResponse[UserResponse],
)
@inject
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    uc: FromDishka[CreateUserUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(UserPermission.CREATE))],
):
    """Create a new user (and auth account)."""
    user = await uc.execute(user_data, background_tasks)
    return ApiResponse.success(
        data=UserResponse.model_validate(user), message="User created successfully"
    )


@router.post("/import", response_model=ApiResponse[UserImportResult])
@inject
async def import_users(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    uc: FromDishka[ImportUsersUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(UserPermission.CREATE))],
):
    """Bulk import users from file."""
    result = await uc.execute(file, background_tasks)
    return ApiResponse.success(data=result, message="User import completed")


@router.post("/me/avatar", response_model=ApiResponse[UserResponse])
@inject
async def update_avatar(
    file: UploadFile,
    uc: FromDishka[UpdateAvatarUseCase],
    current_user: CurrentUser,
):
    """Upload and set user avatar."""
    assert current_user.id is not None
    user = await uc.execute(current_user.id, file)
    return ApiResponse.success(
        data=UserResponse.model_validate(user), message="Avatar updated successfully"
    )


@router.put("/{user_id}", response_model=ApiResponse[UserResponse])
@inject
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    uc: FromDishka[UpdateUserUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(UserPermission.UPDATE))],
):
    """Update user information."""
    updated = uc.execute(user_id, **user_data.model_dump(exclude_unset=True))
    return ApiResponse.success(
        data=UserResponse.model_validate(updated), message="User updated successfully"
    )


@router.delete("/{user_id}", response_model=ApiResponse[bool])
@inject
async def delete_user(
    user_id: int,
    uc: FromDishka[DeleteUserUseCase],
    _: Annotated[CurrentUser, Depends(PermissionChecker(UserPermission.DELETE))],
):
    """Delete a user account."""
    success = uc.execute(user_id)
    return ApiResponse.success(data=success, message="User deleted successfully")


@router.put(
    "/me/settings",
    response_model=ApiResponse[UserResponse],
)
@inject
async def update_me(
    settings_data: UserSettingsUpdate,
    current_user: CurrentUser,
    uc: FromDishka[UpdateUserUseCase],
):
    """Cập nhật cài đặt cá nhân (avatar_url, discord_id, check_in_card_code)."""
    assert current_user.id is not None
    updated = uc.execute(
        current_user.id, **settings_data.model_dump(exclude_unset=True)
    )
    return ApiResponse.success(
        data=UserResponse.model_validate(updated),
        message="Settings updated successfully",
        status_code=200,
    )
