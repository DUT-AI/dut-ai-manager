from app.auth.application.dtos import CurrentUserDTO
from app.auth.domain.interfaces import ITokenService
from fastapi import HTTPException, Request, status


def _extract_token(request: Request) -> str:
    """Extract JWT from cookie first, then fallback to Authorization header."""
    # 1. Try cookie
    token = request.cookies.get("access_token")
    if token:
        return token

    # 2. Fallback to Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ")[1]

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Not authenticated",
    )


async def get_current_user(request: Request) -> CurrentUserDTO:
    """Get full user info from JWT claims (cookie or header)."""
    token = _extract_token(request)

    try:
        container = request.state.dishka_container
        token_service = await container.get(ITokenService)
        token_data = token_service.decode_token(token)

        return CurrentUserDTO(
            id=int(token_data["sub"]),
            email=token_data.get("email", ""),
            name=token_data.get("name", ""),
            avatar_url=token_data.get("avatar", ""),
            role_name=token_data.get("role"),
            permissions=token_data.get("permissions", []),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from e
