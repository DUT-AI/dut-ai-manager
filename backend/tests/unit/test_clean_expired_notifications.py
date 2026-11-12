from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from app.reminder.application.clean_expired_notifications_use_case import (
    CleanExpiredNotificationsUseCase,
)


@pytest.mark.asyncio
async def test_clean_expired_notifications_use_case():
    repo = MagicMock()
    repo.delete_read_before.return_value = 15

    use_case = CleanExpiredNotificationsUseCase(notification_repo=repo)
    result = await use_case.execute(retention_days=30)

    assert result == 15
    assert repo.delete_read_before.called
    cutoff_arg = repo.delete_read_before.call_args.kwargs["cutoff"]
    now = datetime.now(UTC)
    # Cutoff phải xấp xỉ 30 ngày trước
    assert (now - cutoff_arg).days == 30
