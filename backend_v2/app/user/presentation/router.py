from typing import List

from app.shared.api_response import ApiResponse
from app.user.application.dtos import (UserCreateDTO, UserImportResultDTO,
                                       UserResponseDTO, UserSettingsUpdateDTO,
                                       UserUpdateDTO)
from app.user.application.use_cases.create_user import CreateUserUseCase
from app.user.application.use_cases.delete_user import DeleteUserUseCase
from app.user.application.use_cases.get_users import (GetUserByIdUseCase,
                                                      GetUsersUseCase)
from app.user.application.use_cases.import_users import ImportUsersUseCase
from app.user.application.use_cases.update_user import (
  UpdateUserAvatarUseCase, UpdateUserSettingsUseCase, UpdateUserUseCase)
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, UploadFile

router = APIRouter(prefix="/users", tags=["users"])


class CurrentUser:
    id: int = 1


def get_current_user() -> CurrentUser:
    return CurrentUser()


@router.get("", response_model=ApiResponse[List[UserResponseDTO]])
@inject
async def get_users(use_case: FromDishka[GetUsersUseCase]):
    """Retrieve all users"""
    data = await use_case.execute()
    return ApiResponse.success(data=data)


@router.get("/{user_id}", response_model=ApiResponse[UserResponseDTO])
@inject
async def get_user(user_id: int, use_case: FromDishka[GetUserByIdUseCase]):
    """Get a specific user by ID"""
    data = await use_case.execute(user_id)
    return ApiResponse.success(data=data)


@router.post("", response_model=ApiResponse[UserResponseDTO], status_code=201)
@inject
async def create_user(
    user_data: UserCreateDTO, use_case: FromDishka[CreateUserUseCase]
):
    """Create a new user"""
    data = await use_case.execute(user_data)
    return ApiResponse.created(data=data)


@router.post("/import", response_model=ApiResponse[UserImportResultDTO])
@inject
async def import_users(file: UploadFile, use_case: FromDishka[ImportUsersUseCase]):
    """Import users from Excel file"""
    data = await use_case.execute(file)
    return ApiResponse.success(data=data)


@router.put("/me/settings", response_model=ApiResponse[UserResponseDTO])
@inject
async def update_me(
    settings_data: UserSettingsUpdateDTO,
    use_case: FromDishka[UpdateUserSettingsUseCase],
    current_user: CurrentUser = Depends(get_current_user),
):
    """Update current user's settings (avatar and discord_id)"""
    data = await use_case.execute(current_user.id, settings_data)
    return ApiResponse.success(data=data)


@router.post("/me/avatar", response_model=ApiResponse[UserResponseDTO])
@inject
async def update_avatar_me(
    file: UploadFile,
    use_case: FromDishka[UpdateUserAvatarUseCase],
    current_user: CurrentUser = Depends(get_current_user),
):
    """Upload avatar for current user"""
    data = await use_case.execute(current_user.id, file)
    return ApiResponse.success(data=data)


@router.put("/{user_id}", response_model=ApiResponse[UserResponseDTO])
@inject
async def update_user(
    user_id: int, user_data: UserUpdateDTO, use_case: FromDishka[UpdateUserUseCase]
):
    """Update a user"""
    data = await use_case.execute(user_id, user_data)
    return ApiResponse.success(data=data)


@router.delete("/{user_id}", response_model=ApiResponse[None])
@inject
async def delete_user(user_id: int, use_case: FromDishka[DeleteUserUseCase]):
    """Delete a user"""
    await use_case.execute(user_id)
    return ApiResponse.success(message="User deleted successfully")
