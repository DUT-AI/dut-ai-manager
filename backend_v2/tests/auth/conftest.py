import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def session():
    """Cung cấp một AsyncMock session cho integration tests."""
    return AsyncMock()
