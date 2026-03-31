"""
Backward compatibility — alias UserModel from module.
New code should import from app.user.infrastructure.model
"""

from app.user.infrastructure.model import UserModel as User, UserStatus

__all__ = ["User", "UserStatus"]
