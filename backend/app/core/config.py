import secrets
from typing import Annotated, Any, Literal

from pydantic import (
    AnyUrl,
    BeforeValidator,
    PostgresDsn,
    computed_field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict


def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",") if i.strip()]
    elif isinstance(v, list | str):
        return v
    raise ValueError(v)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Use top level .env file (one level above ./backend/)
        env_file="../.env",
        env_ignore_empty=True,
        extra="ignore",
    )

    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8
    FRONTEND_HOST: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"

    # MinIO Configuration
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = ""
    MINIO_SECRET_KEY: str = ""
    MINIO_BUCKET_NAME: str = "homework-submissions"
    MINIO_SECURE: bool = False

    # Meeting Configuration
    MAX_SEATS: int = 30

    # Discord Bot Configuration
    DISCORD_BOT_TOKEN: str = ""
    DISCORD_PERMISSION_ROOM_ID: str = ""

    # Email / SMTP Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    EMAILS_FROM_EMAIL: str = ""
    EMAILS_FROM_NAME: str = "DUT AI Manager"

    BACKEND_CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_cors)] = (
        []
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

    # Base PostgreSQL config
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432

    # Production Database credentials
    POSTGRES_DB: str = ""
    POSTGRES_USER_ADMIN: str = ""
    POSTGRES_PASSWORD_ADMIN: str = ""

    # Development Database credentials
    POSTGRES_DEV_DB: str = ""
    POSTGRES_USER_DEV: str = ""
    POSTGRES_PASSWORD_DEV: str = ""

    @computed_field  # type: ignore[prop-decorator]
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        # Select credentials based on environment
        if self.ENVIRONMENT == "production":
            db_user = self.POSTGRES_USER_ADMIN
            db_password = self.POSTGRES_PASSWORD_ADMIN
            db_name = self.POSTGRES_DB
        else:
            db_user = self.POSTGRES_USER_DEV
            db_password = self.POSTGRES_PASSWORD_DEV
            db_name = self.POSTGRES_DEV_DB

        return PostgresDsn.build(
            scheme="postgresql+psycopg",
            username=db_user,
            password=db_password,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=db_name,
        )


settings = Settings()
