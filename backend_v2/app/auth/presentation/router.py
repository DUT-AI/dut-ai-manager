from app.auth.application.dtos import (ChangePasswordRequestDTO,
                                       CurrentUserDTO, LoginRequestDTO,
                                       RefreshTokenRequestDTO,
                                       TokenResponseDTO)
from app.auth.application.use_cases.change_password import \
  ChangePasswordUseCase
from app.auth.application.use_cases.login import LoginUseCase
from app.auth.application.use_cases.refresh_token import RefreshTokenUseCase
from app.auth.infrastructure.security import (get_current_user,
                                               get_current_user_id)
from app.settings import JWTSetting
from app.shared.api_response import ApiResponse
from app.user.application.dtos import UserResponseDTO
from dishka.integrations.fastapi import FromDishka, inject
from fastapi import APIRouter, Depends, Response

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=ApiResponse[TokenResponseDTO])
@inject
async def login(
    payload: LoginRequestDTO,
    response: Response,
    use_case: FromDishka[LoginUseCase],
    jwt_settings: FromDishka[JWTSetting],
):
    data = await use_case.execute(payload)

    response.set_cookie(
        key="access_token",
        value=data.access_token,
        httponly=True,
        secure=False,  # Should be True in production with HTTPS
        samesite="lax",
        max_age=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=data.refresh_token,
        httponly=True,
        secure=False,  # Should be True in production with HTTPS
        samesite="lax",
        max_age=jwt_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return ApiResponse.success(data=data)


@router.post("/refresh", response_model=ApiResponse[TokenResponseDTO])
@inject
async def refresh_token(
    payload: RefreshTokenRequestDTO,
    response: Response,
    use_case: FromDishka[RefreshTokenUseCase],
    jwt_settings: FromDishka[JWTSetting],
):
    data = await use_case.execute(payload)

    response.set_cookie(
        key="access_token",
        value=data.access_token,
        httponly=True,
        secure=False,  # Should be True in production with HTTPS
        samesite="lax",
        max_age=jwt_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=data.refresh_token,
        httponly=True,
        secure=False,  # Should be True in production with HTTPS
        samesite="lax",
        max_age=jwt_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return ApiResponse.success(data=data)


@router.post("/logout", response_model=ApiResponse[None])
async def logout(response: Response):
    """Logout by clearing cookies."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return ApiResponse.success(message="Successfully logged out")


@router.post("/change-password")
@inject
async def change_password(
    payload: ChangePasswordRequestDTO,
    use_case: FromDishka[ChangePasswordUseCase],
    user_id: int = Depends(get_current_user_id),
):
    await use_case.execute(user_id, payload)
    return ApiResponse.success(data=True)


@router.get("/me", response_model=ApiResponse[UserResponseDTO])
async def get_me(current_user: CurrentUserDTO = Depends(get_current_user)):
    """Get current user info using JWT claims."""
    # Use JWT claims to avoid lazy loading DB queries
    return ApiResponse.success(
        data=UserResponseDTO(
            id=current_user.id,
            name=current_user.name,
            email=current_user.email,
            role_name=current_user.role_name,
            avatar_url=current_user.avatar_url,
            permissions=current_user.permissions,
        ),
    )
