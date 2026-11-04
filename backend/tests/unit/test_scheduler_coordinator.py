from unittest.mock import AsyncMock

import pytest

from app.core.scheduler_coordinator import RedisSchedulerCoordinator
from app.core.scheduler_types import LeaderRole, WorkerIdentity


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    # Default set returns True for acquiring lock
    redis.set = AsyncMock(return_value=True)
    redis.eval = AsyncMock(return_value=1)
    redis.get = AsyncMock(return_value=None)
    return redis


@pytest.fixture
def mock_dishka_container():
    return AsyncMock()


@pytest.fixture
def coordinator(mock_redis, mock_dishka_container):
    identity = WorkerIdentity(hostname="test-host", pid=1234, instance_id="abcd1234")
    return RedisSchedulerCoordinator(
        redis_client=mock_redis,
        dishka_container=mock_dishka_container,
        identity=identity,
    )


@pytest.mark.asyncio
async def test_acquire_leadership_success(coordinator, mock_redis):
    mock_redis.set.return_value = True

    acquired = await coordinator.acquire_leadership()

    assert acquired is True
    assert coordinator.role == LeaderRole.LEADER
    assert coordinator.is_leader is True
    mock_redis.set.assert_awaited_once_with(
        "dut_ai:scheduler:leader_lock",
        "test-host:1234:abcd1234",
        nx=True,
        ex=30,
    )


@pytest.mark.asyncio
async def test_acquire_leadership_already_held_by_other(coordinator, mock_redis):
    mock_redis.set.return_value = False

    acquired = await coordinator.acquire_leadership()

    assert acquired is False
    assert coordinator.role == LeaderRole.STANDBY
    assert coordinator.is_leader is False


@pytest.mark.asyncio
async def test_release_leadership_when_leader(coordinator, mock_redis):
    # First become leader
    mock_redis.set.return_value = True
    await coordinator.acquire_leadership()

    mock_redis.eval.return_value = 1
    released = await coordinator.release_leadership()

    assert released is True
    assert coordinator.role == LeaderRole.STANDBY
    mock_redis.eval.assert_awaited_once()


@pytest.mark.asyncio
async def test_release_leadership_when_not_leader(coordinator, mock_redis):
    # Never acquired leadership
    released = await coordinator.release_leadership()

    assert released is False
    mock_redis.eval.assert_not_awaited()


@pytest.mark.asyncio
async def test_renew_leadership_success(coordinator, mock_redis):
    # Setup leader
    mock_redis.set.return_value = True
    await coordinator.acquire_leadership()

    mock_redis.eval.return_value = 1
    renewed = await coordinator._renew_leadership()

    assert renewed is True
    mock_redis.eval.assert_awaited_once()


@pytest.mark.asyncio
async def test_renew_leadership_failed(coordinator, mock_redis):
    mock_redis.set.return_value = True
    await coordinator.acquire_leadership()

    mock_redis.eval.return_value = 0
    renewed = await coordinator._renew_leadership()

    assert renewed is False


@pytest.mark.asyncio
async def test_redis_connection_error_graceful_degradation(coordinator, mock_redis):
    mock_redis.set.side_effect = ConnectionError("Redis server unreachable")

    acquired = await coordinator.acquire_leadership()

    # Must NOT raise exception, just return False and stay in Standby
    assert acquired is False
    assert coordinator.role == LeaderRole.STANDBY


@pytest.mark.asyncio
async def test_start_and_stop_lifecycle(coordinator, mock_redis):
    mock_redis.set.return_value = True
    mock_redis.eval.return_value = 1

    await coordinator.start()

    assert coordinator.is_leader is True
    assert coordinator.state.heartbeat_task is not None
    assert coordinator.state.is_running is True

    await coordinator.stop()

    assert coordinator.state.is_running is False
    assert coordinator.is_leader is False
