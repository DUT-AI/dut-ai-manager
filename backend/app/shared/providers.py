from typing import Iterable

from dishka import Provider, Scope, provide
from sqlmodel import Session, create_engine
from app.core.config import settings
from app.shared.infrastructure.email_service import EmailService
from app.shared.infrastructure.minio_service import MinioService
from app.shared.infrastructure.discord_service import DiscordService
from sqlalchemy.engine import Engine


class InfrastructureProvider(Provider):
    @provide(scope=Scope.APP)
    def get_engine(self) -> Engine:
        return create_engine(
            str(settings.SQLALCHEMY_DATABASE_URI),
            echo=settings.ENVIRONMENT == "local",
        )

    @provide(scope=Scope.REQUEST)
    def get_session(self, engine: Engine) -> Iterable[Session]:
        with Session(engine) as session:
            try:
                yield session
                session.commit()
            except Exception:
                session.rollback()
                raise

    @provide(scope=Scope.APP)
    def get_email_service(self) -> EmailService:
        return EmailService()

    @provide(scope=Scope.APP)
    def get_minio_service(self) -> MinioService:
        return MinioService()

    @provide(scope=Scope.APP)
    def get_discord_service(self) -> DiscordService:
        return DiscordService()
