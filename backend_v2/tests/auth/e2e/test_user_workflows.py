import pytest

@pytest.mark.asyncio
async def test_full_login_and_password_change_flow():
    # E2E test simulating:
    # 1. Login to get token
    # 2. Use token to call protected endpoint
    # 3. Change password
    # 4. Login with new password
    pass
