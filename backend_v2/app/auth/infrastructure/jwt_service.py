from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import jwt
from app.auth.domain.interfaces import ITokenService
from app.settings import JWTSetting


class JwtTokenService(ITokenService):
    def __init__(self, settings: JWTSetting):
        self.secret_key = settings.SECRET_KEY
        self.access_expire_minutes = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_expire_minutes = 60 * 24 * 30  # 30 days
        self.algorithm = "HS256"

    def create_access_token(self, payload: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.access_expire_minutes)
        claims = {"exp": expire, "type": "access"}
        claims.update(payload)
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

    def create_refresh_token(self, payload: dict) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=self.refresh_expire_minutes)
        claims = {"exp": expire, "type": "refresh"}
        claims.update(payload)
        return jwt.encode(claims, self.secret_key, algorithm=self.algorithm)

    def decode_token(self, token: str) -> Dict[str, Any]:
        return jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
