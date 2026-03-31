from unittest.mock import AsyncMock

import pytest


@pytest.fixture
def session():
    """Cung cấp một AsyncMock session cho integration tests."""
    return AsyncMock()
