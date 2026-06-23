from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format"""

    is_success: bool
    status_code: int
    data: T | None = None
    message: str

    @classmethod
    def success(
        cls,
        data: T | None = None,
        message: str = "Success",
        status_code: int = 200,
    ) -> "ApiResponse[T]":
        """Create a success response"""
        return cls(
            is_success=True,
            status_code=status_code,
            data=data,
            message=message,
        )

    @classmethod
    def error(
        cls,
        message: str = "Error",
        status_code: int = 400,
        data: T | None = None,
    ) -> "ApiResponse[T]":
        """Create an error response"""
        return cls(
            is_success=False,
            status_code=status_code,
            data=data,
            message=message,
        )

    @classmethod
    def created(
        cls,
        data: T | None = None,
        message: str = "Created",
        status_code: int = 201,
    ) -> "ApiResponse[T]":
        """Create a created response"""
        return cls(
            is_success=True,
            status_code=status_code,
            data=data,
            message=message,
        )


class BadRequestException(Exception):
    """Custom exception for bad requests"""

    def __init__(self, message: str, data: Any | None = None, status_code: int = 400):
        self.message = message
        self.data = data
        self.status_code = status_code


class UserInfoResponse(BaseModel):
    """Response model for user information"""

    id: int
    name: str
    email: str | None = None
    avatar_url: str | None = None

    class Config:
        from_attributes = True
