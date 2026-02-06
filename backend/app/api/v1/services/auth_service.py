import random
import string
from datetime import timedelta
from typing import Optional, Tuple

from app.api.v1.repositories import AccountRepository, UserRepository
from app.core.config import settings
from app.models import Account, User, UserStatus
from app.schemas.response import BadRequestException
from app.utils.password import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    hash_password,
    verify_password,
)


class AuthService:
    """Service for authentication operations"""

    def __init__(
        self,
        user_repository: UserRepository,
        account_repository: AccountRepository,
    ):
        self.user_repository = user_repository
        self.account_repository = account_repository

    def authenticate(self, email: str, password: str):
        """
        Authenticate user with email and password.
        Returns: (success, user, message)
        """
        # Find user by email
        user = self.user_repository.get_by_email(email)

        if not user or not user.account_id:
            raise BadRequestException("User not found or user has no account")

        if user.status == UserStatus.INACTIVE:
            raise BadRequestException("Account is inactive")

        # Get account
        account = self.account_repository.get_by_id(user.account_id)

        if not account:
            raise BadRequestException("Account not found")

        # Verify password
        if not verify_password(password, account.hash_password):
            raise BadRequestException("Incorrect email or password")

        return user

    def create_tokens(self, user: User) -> Tuple[str, str]:
        """Create access and refresh tokens for user with embedded user info"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

        # Build extra claims for JWT
        extra_claims = {
            "name": user.name,
            "role": user.role.name if user.role else None,
            "avatar": user.avatar_url,
            "permissions": list(user.permissions) if user.role else [],
        }

        access_token = create_access_token(
            subject=user.id,
            expires_delta=access_token_expires,
            extra_claims=extra_claims,
        )
        refresh_token = create_refresh_token(subject=user.id)
        return access_token, refresh_token

    def refresh_tokens(self, refresh_token_str: str) -> Optional[Tuple[str, str]]:
        """
        Refresh tokens using refresh token.
        Returns: (success, (access_token, refresh_token) or None, message)
        """
        payload = decode_token(refresh_token_str)

        if not payload:
            raise BadRequestException("Invalid or expired refresh token")

        if payload.get("type") != "refresh":
            raise BadRequestException("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise BadRequestException("Invalid token payload")

        user = self.user_repository.get_by_id(int(user_id))

        if not user:
            raise BadRequestException("User not found")

        tokens = self.create_tokens(user)
        return tokens

    def get_user_from_token(self, token: str) -> Optional[User]:
        """
        Get user from access token.
        Returns: (success, user, message)
        """
        payload = decode_token(token)

        if not payload:
            raise BadRequestException("Invalid or expired token")

        if payload.get("type") != "access":
            raise BadRequestException("Invalid token type")

        user_id = payload.get("sub")
        if not user_id:
            raise BadRequestException("Invalid token payload")

        user = self.user_repository.get_by_id(int(user_id))

        if not user:
            raise BadRequestException("User not found")

        return user

    def create_account(self) -> Tuple[Account, str]:
        """
        Create a new account.
        Returns: (success, account, message)
        """
        # Generate strong password
        password = self.generate_strong_password()
        account = Account(hash_password=hash_password(password))
        return self.account_repository.create(account), password

    def change_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> None:
        """
        Change user password.
        Returns: (success, message)
        """
        user = self.user_repository.get_by_id(user_id)
        if not user or not user.account_id:
            raise BadRequestException("Not found user or account!")

        account = self.account_repository.get_by_id(user.account_id)
        if not account:
            raise BadRequestException("Not found account!")

        if not verify_password(old_password, account.hash_password):
            raise BadRequestException("Sai mật khẩu cũ")

        account.hash_password = get_password_hash(new_password)
        self.account_repository.update(account)

    def delete_account(self, account_id: int) -> None:
        account = self.account_repository.get_by_id(account_id)
        if not account:
            raise BadRequestException("Account not found")
        self.account_repository.delete_by_id(account_id)

    def generate_strong_password(self) -> str:
        """Generate a random strong password specific format: Xyz@123..."""

        # Define character sets
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        symbols = "@#$!%*?&"

        # Ensure at least one of each required type
        password_chars = [
            random.choice(uppercase),
            random.choice(lowercase),
            random.choice(digits),
            random.choice(symbols),
        ]

        # Fill the rest with a mix
        all_chars = lowercase + uppercase + digits + symbols
        # Length between 10 and 12
        length = random.randint(10, 12)

        for _ in range(length - 4):
            password_chars.append(random.choice(all_chars))

        # Shuffle
        random.shuffle(password_chars)
        return "".join(password_chars)
