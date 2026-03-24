from app.shared.base_exception import DomainException


class InvalidCredentialsException(DomainException):
    def __init__(self, message="Email hoặc mật khẩu không chính xác"):
        super().__init__(message=message, status_code=401)


class InvalidTokenException(DomainException):
    def __init__(self, message="Token không hợp lệ hoặc đã hết hạn"):
        super().__init__(message=message, status_code=401)


class UserInactiveException(DomainException):
    def __init__(self, message="Tài khoản này đã bị khóa"):
        super().__init__(message=message, status_code=403)
