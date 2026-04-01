from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format"""

    is_success: bool
    status_code: int
    data: Optional[T] = None
    message: str

    @classmethod
    def success(
        cls,
        data: Optional[T] = None,
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
        data: Optional[T] = None,
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
        data: Optional[T] = None,
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
    def __init__(self, message: str, data: Any | None = None, status_code: int = 400):
        self.message = message
        self.data = data
        self.status_code = status_code
