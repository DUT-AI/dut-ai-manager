"""SharedProvider — provides cross-cutting infrastructure (EventBus, EmailService)."""

from app.settings import CommonSettings, SMTPSetting
from app.shared.email_service import IEmailService
from app.shared.event_bus import IEventBus
from app.shared.infrastructure.simple_event_bus import SimpleEventBus
from app.shared.infrastructure.smtp_email_service import SmtpEmailService
from app.user.application.event_handlers import SendWelcomeEmailHandler
from app.user.domain.events import UserCreatedEvent
from dishka import Provider, Scope, provide


class SharedProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_smtp_settings(self) -> SMTPSetting:
        return SMTPSetting()

    @provide(scope=Scope.APP)
    def provide_common_settings(self) -> CommonSettings:
        return CommonSettings()

    @provide(scope=Scope.APP)
    def provide_email_service(
        self, smtp: SMTPSetting, common: CommonSettings
    ) -> IEmailService:
        return SmtpEmailService(smtp, common)

    @provide(scope=Scope.APP)
    def provide_event_bus(self, email_service: IEmailService) -> IEventBus:
        bus = SimpleEventBus()
        # Register event handlers
        bus.subscribe(
            UserCreatedEvent,
            SendWelcomeEmailHandler(email_service),  # type: ignore[arg-type]
        )
        return bus

