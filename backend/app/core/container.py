from app.core.discord_service import DiscordService
from app.core.minio_service import MinioService
from app.api.v1.services.email_service import EmailService


class AppContainer:
    """Container for global application services."""

    def __init__(self):
        self.minio_service = MinioService()
        self.discord_service = DiscordService()
        self.email_service = EmailService()
