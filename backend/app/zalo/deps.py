from typing import Annotated

from app.shared.infrastructure.database import get_session
from app.user.infrastructure.repository import UserRepository
from app.zalo.application.use_cases import (BindZaloAccountUseCase,
                                            GenerateBotBindCodeUseCase,
                                            GetZaloLoginUrlUseCase,
                                            HandleBotWebhookUseCase,
                                            SendZaloNotificationUseCase)
from app.zalo.infrastructure.zalo_bot_client import ZaloBotClient
from app.zalo.infrastructure.zalo_client import ZaloClient
from fastapi import Depends
from sqlmodel import Session


def get_zalo_client() -> ZaloClient:
    return ZaloClient()


def get_zalo_bot_client() -> ZaloBotClient:
    return ZaloBotClient()


def get_login_url_uc() -> GetZaloLoginUrlUseCase:
    return GetZaloLoginUrlUseCase()


def get_bind_account_uc(
    zalo_client: Annotated[ZaloClient, Depends(get_zalo_client)],
    session: Annotated[Session, Depends(get_session)],
) -> BindZaloAccountUseCase:
    user_repo = UserRepository(session)
    return BindZaloAccountUseCase(zalo_client, user_repo)


def get_generate_bot_code_uc(
    session: Annotated[Session, Depends(get_session)],
) -> GenerateBotBindCodeUseCase:
    user_repo = UserRepository(session)
    return GenerateBotBindCodeUseCase(user_repo)


def get_handle_bot_webhook_uc(
    bot_client: Annotated[ZaloBotClient, Depends(get_zalo_bot_client)],
    session: Annotated[Session, Depends(get_session)],
) -> HandleBotWebhookUseCase:
    user_repo = UserRepository(session)
    return HandleBotWebhookUseCase(bot_client, user_repo)


def get_send_notification_uc(
    zalo_client: Annotated[ZaloClient, Depends(get_zalo_client)],
    bot_client: Annotated[ZaloBotClient, Depends(get_zalo_bot_client)],
) -> SendZaloNotificationUseCase:
    return SendZaloNotificationUseCase(zalo_client, bot_client)
