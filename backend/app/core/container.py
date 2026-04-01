from app.api.v1.services.email_service import EmailService
from app.core.discord_service import DiscordService
from app.permission_request.infrastructure.repository import \
  PermissionRequestRepository
from app.shared.domain.event_bus import EventBus
from app.shared.infrastructure.database import engine
from app.shared.infrastructure.minio_service import MinioService
from app.violation.application.use_cases import CreateViolationUseCase
from app.violation.infrastructure.repository import ViolationRepository
from app.violation.permission_handler import (PermissionViolationHandler,
                                              register_permission_handlers)
from sqlmodel import Session


class AppContainer:
    """Container for global application services."""

    def __init__(self):
        self.minio_service = MinioService()
        self.discord_service = DiscordService()
        self.email_service = EmailService()

        # Register Domain Event Handlers
        self._register_event_handlers()

    def _register_event_handlers(self):
        # We need a session for repositories inside handlers
        # Usually, handlers are long-lived singleton-like, so they create sessions per use or use a factory
        # For simplicity in this in-process bus, we pass a repo factory or create one.
        # But wait, handlers should ideally be thin and use a session per event or a UseCase.

        with Session(engine) as session:
            violation_repo = ViolationRepository(session)
            permission_repo = PermissionRequestRepository(session)

            create_violation_uc = CreateViolationUseCase(violation_repo)

            permission_handler = PermissionViolationHandler(
                create_violation_uc=create_violation_uc, permission_repo=permission_repo
            )

            register_permission_handlers(EventBus, permission_handler)

        # Register other handlers (ViolationNotification, etc.)
