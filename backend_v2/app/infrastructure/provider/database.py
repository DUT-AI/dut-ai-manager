from typing import Any, AsyncIterable

from app.settings import DatabaseSettings
from app.shared.request_context import current_user_id_var
from dishka import Provider, Scope, provide
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (AsyncEngine, AsyncSession,
                                    async_sessionmaker, create_async_engine)
from sqlalchemy.orm import Session


def _set_audit_fields(session: Session, flush_context: Any, instances: Any) -> None:
    """Auto-populate created_by/updated_by from request context."""
    user_id = current_user_id_var.get(None)

    for obj in session.new:
        if hasattr(obj, "created_by") and obj.created_by is None:
            obj.created_by = user_id
        if hasattr(obj, "updated_by"):
            obj.updated_by = user_id

    for obj in session.dirty:
        if hasattr(obj, "updated_by"):
            obj.updated_by = user_id


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def db_settings(self) -> DatabaseSettings:
        return DatabaseSettings()

    @provide(scope=Scope.APP)
    def async_engine(self, settings: DatabaseSettings) -> AsyncEngine:
        return create_async_engine(
            str(settings.SQLALCHEMY_DATABASE_URI),
            echo=settings.DEBUG,
        )

    @provide(scope=Scope.APP)
    def session_maker(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
        )

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            # Register audit event for this session
            event.listen(session.sync_session, "before_flush", _set_audit_fields)
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
