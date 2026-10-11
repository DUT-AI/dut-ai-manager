from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Metadata for paginated responses"""

    page: int = Field(..., description="Current page number (1-indexed)")
    page_size: int = Field(..., description="Number of items per page")
    total: int = Field(..., description="Total number of matching records")
    total_pages: int = Field(..., description="Total number of available pages")
    has_next: bool = Field(..., description="Whether there is a next page")

    @classmethod
    def create(cls, page: int, page_size: int, total: int) -> "PaginationMeta":
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        has_next = page < total_pages
        return cls(
            page=page,
            page_size=page_size,
            total=total,
            total_pages=total_pages,
            has_next=has_next,
        )


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format"""

    is_success: bool
    status_code: int
    data: T | None = None
    message: str
    pagination: PaginationMeta | None = None

    @classmethod
    def success(
        cls,
        data: T | None = None,
        message: str = "Success",
        status_code: int = 200,
        pagination: PaginationMeta | None = None,
    ) -> "ApiResponse[T]":
        """Create a success response"""
        return cls(
            is_success=True,
            status_code=status_code,
            data=data,
            message=message,
            pagination=pagination,
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
