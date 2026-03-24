"""SharedProvider — provides cross-cutting infrastructure (EventBus, EmailService)."""

from app.shared.email_service import IEmailService
from app.shared.event_bus import IEventBus
from app.shared.infrastructure.simple_event_bus import SimpleEventBus
from app.shared.infrastructure.smtp_email_service import SmtpEmailService
from app.user.application.event_handlers import SendWelcomeEmailHandler
from app.user.domain.events import UserCreatedEvent
from dishka import Provider, Scope, provide


class SharedProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_email_service(self) -> IEmailService:
        return SmtpEmailService()

    @provide(scope=Scope.APP)
    def provide_event_bus(self, email_service: IEmailService) -> IEventBus:
        bus = SimpleEventBus()
        # Register event handlers
        bus.subscribe(
            UserCreatedEvent,
            SendWelcomeEmailHandler(email_service),
        )
        return bus
