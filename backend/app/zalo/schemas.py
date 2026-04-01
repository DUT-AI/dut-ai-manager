from typing import Optional

from pydantic import BaseModel


class ZaloLoginUrlResponse(BaseModel):
    login_url: str
    code_verifier: str


class ZaloBindRequest(BaseModel):
    oauth_code: str
    code_verifier: str


class ZaloBindCodeResponse(BaseModel):
    bind_code: str
