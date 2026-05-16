from pydantic import BaseModel


class ZaloProfile(BaseModel):
    """Thông tin cá nhân từ Zalo Graph API (Domain Entity)"""

    id: str
    name: str = ""


class ZaloOAuthState(BaseModel):
    """Thông tin phiên đăng nhập OAuth PKCE"""

    code_verifier: str
    code_challenge: str
    login_url: str
