from enum import Enum
from typing import Annotated

from app.core.context import set_current_user_id
from app.core.database import get_session
from app.core.repository_factory import RepositoryFactory
from app.core.service_factory import ServiceFactory
from app.models import RoleType, User
from app.schemas.response import BadRequestException
from app.utils.password import decode_token
from fastapi import Depends, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session

security = HTTPBearer(auto_error=False)


def get_token_from_cookie_or_header(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str:
    """Get token from cookie or Authorization header"""
    # Try to get from cookie first
    token = request.cookies.get("access_token")

    # If not in cookie, try Authorization header
    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise BadRequestException(
            status_code=status.HTTP_401_UNAUTHORIZED, message="Not token"
        )

    return token


def get_current_user(
    token: Annotated[str, Depends(get_token_from_cookie_or_header)],
    session: Annotated[Session, Depends(get_session)],
) -> User:
    """
    Get current user from token.
    Supports:
    1. JWT Access Token (User login)
    2. API Key (Role-based system access)
    """
    # 1. Check for API Key format (sk-...)
    if token.startswith("sk-"):
        # We need to manually get service_factory here because we can't inject it easily
        # into a dependency that is used by other dependencies without circular issues or complexity.
        # However, `get_service_factory` requires `request`.
        # Best way: Use the repo factory directly or service factory if possible.
        # Actually, `get_current_user` doesn't have `request` injected, but `get_token...` had `request`.
        # Let's inject `ServiceFactory` or `RepositoryFactory`.
        # Constraint: `get_current_user` signature is used in many places.
        # Better: use `RepositoryFactory` which is lighter.

        # NOTE: WE NEED TO INJECT REPO FACTORY HERE.
        # But wait, `get_current_user` currently only depends on `token` and `session`.
        # We can use `session` to create `RepositoryFactory`.

        repo_factory = RepositoryFactory(session)
        # We need `RoleApiKeyService` logic to verify.
        # Re-implement verification logic here or use Service?
        # Service needs Repo.
        # Let's keep it simple: Use Repo directly to find key.

        prefix = token[:6]  # Match the prefix length in model
        # Use the specific repo method we added
        candidates = repo_factory.role_api_key.get_candidates_by_prefix(prefix)

        matched_key = None
        for key in candidates:
            # We need `verify_password` from utils
            from app.utils.password import verify_password

            if verify_password(token, key.key_hash):
                matched_key = key
                break

        if not matched_key:
            raise BadRequestException("Invalid API Key", status.HTTP_401_UNAUTHORIZED)

        # Create a "System User" stub
        # We need to fetch the role's permissions
        role = matched_key.role

        # Create a fake user object
        system_user = User(
            id=0,  # System ID
            name=f"System: {matched_key.name}",
            email=f"system+{matched_key.id}@dutai.site",
            role_id=role.id,
            role=role,
        )

        # Attach permissions similarly to JWT
        # Since we have the full Role object loaded (eagerly in repo), we can access permissions
        # But `User.permissions` property relies on `self.role.role_permissions`.
        # Ensure `matched_key.role` has `role_permissions` loaded?
        # `selectinload(RoleApiKey.role)` loads Role, but maybe not Role.role_permissions.
        # We might need to fetch Role with permissions.

        full_role = repo_factory.role.get_role_with_permissions(role.id)
        if full_role:
            system_user.role = full_role  # Replace with fully loaded role

        # Set context
        set_current_user_id(0)

        return system_user

    # 2. Regular JWT processing
    payload = decode_token(token)

    if not payload:
        raise BadRequestException(
            "Invalid or expired token", status.HTTP_401_UNAUTHORIZED
        )

    # Check token type
    if payload.get("type") != "access":
        raise BadRequestException("Invalid token type", status.HTTP_401_UNAUTHORIZED)

    user_id = payload.get("sub")
    if not user_id:
        raise BadRequestException("Invalid token payload", status.HTTP_401_UNAUTHORIZED)

    # Get basic user info from DB (minimal query)
    user = session.get(User, int(user_id))

    if not user:
        raise BadRequestException("User not found", status.HTTP_401_UNAUTHORIZED)

    # Attach JWT claims to user for permission checking (avoid DB queries)
    # These are cached from login time
    if role := payload.get("role"):
        user._jwt_role = role
    if permissions := payload.get("permissions"):
        user._jwt_permissions = set(permissions)
    if name := payload.get("name"):
        user._jwt_name = name
    if avatar := payload.get("avatar"):
        user._jwt_avatar = avatar

    # Set current user ID in context for audit fields
    set_current_user_id(user.id)

    return user


# Type alias for dependency injection
CurrentUser = Annotated[User, Depends(get_current_user)]


class PermissionChecker:
    def __init__(self, permission: str | Enum):
        self.permission = (
            permission.value if isinstance(permission, Enum) else permission
        )

    def __call__(self, current_user: CurrentUser) -> User:
        # Use JWT claims for role/permissions (no DB query needed)
        jwt_role = getattr(current_user, "_jwt_role", None)
        jwt_permissions = getattr(current_user, "_jwt_permissions", set())

        if not jwt_role:
            raise BadRequestException(
                status_code=status.HTTP_403_FORBIDDEN,
                message="User has no role assigned",
            )

        # Check if user is admin (admin has all permissions)
        if jwt_role == RoleType.ADMIN.value:
            return current_user

        # Check specific permission using JWT claims
        if self.permission not in jwt_permissions:
            raise BadRequestException(
                status_code=status.HTTP_403_FORBIDDEN,
                message=f"Missing required permission: {self.permission}",
            )

        return current_user


def hasPermission(permission: str):
    """Dependency factory to check for a specific permission"""
    return Depends(PermissionChecker(permission))


def get_repo_factory(
    session: Annotated[Session, Depends(get_session)],
) -> RepositoryFactory:
    return RepositoryFactory(session)


def get_service_factory(
    request: Request,
    repo_factory: Annotated[RepositoryFactory, Depends(get_repo_factory)],
) -> ServiceFactory:
    container = request.app.state.container
    return ServiceFactory(
        repo_factory,
        minio_service=container.minio_service,
        discord_service=container.discord_service,
        email_service=container.email_service,
    )


ServiceFactoryDI = Annotated[ServiceFactory, Depends(get_service_factory)]


def hasTeamLeaderAccess(target_user_id_param: str = "user_id"):
    async def dependency(
        request: Request, current_user: CurrentUser, service_factory: ServiceFactoryDI
    ):
        jwt_role = getattr(current_user, "_jwt_role", None)
        if jwt_role != RoleType.LEADER.value:
            return  # Admin/other roles bypass

        # Try to get from query params first, then from body
        target_user_id = request.query_params.get(target_user_id_param)
        if not target_user_id:
            data = await request.json()
            target_user_id = data.get(target_user_id_param)
        # Check team membership...
        in_same_team = service_factory.team.is_in_same_team(
            current_user.id, int(target_user_id)
        )
        if not in_same_team:
            raise BadRequestException(
                "Không có quyền vì không chung team",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return Depends(dependency)


def onlyEditOrDeleteYourself(target_user_id_param: str = "user_id"):
    async def dependency(request: Request, current_user: CurrentUser):
        jwt_role = getattr(current_user, "_jwt_role", None)
        if jwt_role != RoleType.LEADER.value:
            return  # Admin/other roles bypass

        # Try to get from query params first, then from body
        target_user_id = request.query_params.get(target_user_id_param)
        if not target_user_id:
            data = await request.json()
            target_user_id = data.get(target_user_id_param)
        # Check team membership...
        if current_user.id != int(target_user_id):
            raise BadRequestException(
                "Chỉ được edit thông tin bản thân",
                status_code=status.HTTP_403_FORBIDDEN,
            )

    return Depends(dependency)
