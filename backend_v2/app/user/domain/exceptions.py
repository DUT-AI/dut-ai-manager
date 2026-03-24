from app.shared.base_exception import DomainException


class UserDomainException(DomainException):
    """Base exception for User domain module"""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message, status_code)


class UserAlreadyExistsException(UserDomainException):
    """Raised when trying to create a user with an email that is already registered."""

    def __init__(self, email: str):
        self.email = email
        super().__init__(f"User with email '{email}' already exists.", 400)


class UserNotFoundException(UserDomainException):
    """Raised when a requested user cannot be found in the system."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User with ID {user_id} not found.", 404)
