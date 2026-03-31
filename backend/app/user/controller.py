"""
User Web Controller — provides API routes.
"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, Query, UploadFile, BackgroundTasks
from sqlmodel import Session

from app.user.domain.entity import User, UserStatus
from app.user.deps import (
    get_user_uc, 
    update_user_uc, 
    delete_user_uc,
    create_user_uc,
    import_users_uc,
    update_avatar_uc
)
from app.user.application.use_cases import (
    GetUserUseCase,
    UpdateUserUseCase,
    DeleteUserUseCase,
    CreateUserUseCase,
    ImportUsersUseCase,
    UpdateAvatarUseCase
)
from app.schemas.user import UserResponse, UserUpdate, UserCreate, UserImportResult
from app.schemas.response import ApiResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=ApiResponse)
async def list_users(
    uc: Annotated[GetUserUseCase, Depends(get_user_uc)],
    keyword: Optional[str] = Query(None, description="Search by name or email")
):
    """List all users or search by keyword."""
    if keyword:
        users = uc.search(keyword)
    else:
        users = uc.get_all()
        
    return ApiResponse(
        data=[UserResponse.model_validate(u) for u in users],
        message="Fetched users successfully"
    )


@router.get("/{user_id}", response_model=ApiResponse)
async def get_user_by_id(
    user_id: int,
    uc: Annotated[GetUserUseCase, Depends(get_user_uc)]
):
    """Retrieve a specific user by ID."""
    user = uc.execute(user_id)
    return ApiResponse(
        data=UserResponse.model_validate(user),
        message="Fetched user profile"
    )


@router.post("", response_model=ApiResponse)
async def create_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    uc: Annotated[CreateUserUseCase, Depends(create_user_uc)]
):
    """Create a new user (and auth account)."""
    user = await uc.execute(user_data, background_tasks)
    return ApiResponse(
        data=UserResponse.model_validate(user),
        message="User created successfully"
    )


@router.post("/import", response_model=ApiResponse)
async def import_users(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    uc: Annotated[ImportUsersUseCase, Depends(import_users_uc)]
):
    """Bulk import users from file."""
    result = await uc.execute(file, background_tasks)
    return ApiResponse(
        data=result,
        message="User import completed"
    )


@router.post("/{user_id}/avatar", response_model=ApiResponse)
async def update_avatar(
    user_id: int,
    file: UploadFile,
    uc: Annotated[UpdateAvatarUseCase, Depends(update_avatar_uc)]
):
    """Upload and set user avatar."""
    user = await uc.execute(user_id, file)
    return ApiResponse(
        data=UserResponse.model_validate(user),
        message="Avatar updated successfully"
    )


@router.patch("/{user_id}", response_model=ApiResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    uc: Annotated[UpdateUserUseCase, Depends(update_user_uc)]
):
    """Update user information."""
    updated = uc.execute(user_id, **user_data.model_dump(exclude_unset=True))
    return ApiResponse(
        data=UserResponse.model_validate(updated),
        message="User updated successfully"
    )


@router.delete("/{user_id}", response_model=ApiResponse)
async def delete_user(
    user_id: int,
    uc: Annotated[DeleteUserUseCase, Depends(delete_user_uc)]
):
    """Delete a user account."""
    success = uc.execute(user_id)
    return ApiResponse(
        data={"success": success},
        message="User deleted successfully"
    )
