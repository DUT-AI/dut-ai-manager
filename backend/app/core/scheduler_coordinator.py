import asyncio
from typing import TYPE_CHECKING

from loguru import logger
from redis.asyncio import Redis

from app.core.scheduler_types import (
    LeaderRole,
    SchedulerCoordinatorState,
    WorkerIdentity,
)

if TYPE_CHECKING:
    from dishka import AsyncContainer

# Lua script to release lock only if the current value matches our worker_id
RELEASE_LOCK_LUA_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""

# Lua script to extend lock TTL only if the current value matches our worker_id
RENEW_LOCK_LUA_SCRIPT = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("expire", KEYS[1], ARGV[2])
else
    return 0
end
"""


class RedisSchedulerCoordinator:
    """Coordinates APScheduler execution across multiple worker processes using Redis Leader Election."""

    def __init__(
        self,
        redis_client: Redis,
        dishka_container: "AsyncContainer",
        identity: WorkerIdentity | None = None,
        lock_key: str = "dut_ai:scheduler:leader_lock",
        lock_ttl: int = 30,
        heartbeat_interval: int = 10,
        standby_poll_interval: int = 10,
    ) -> None:
        self.redis_client = redis_client
        self.dishka_container = dishka_container
        self.identity = identity or WorkerIdentity.create()
        self.lock_key = lock_key
        self.lock_ttl = lock_ttl
        self.heartbeat_interval = heartbeat_interval
        self.standby_poll_interval = standby_poll_interval

        self.state = SchedulerCoordinatorState(worker_id=self.identity.worker_id)

    @property
    def worker_id(self) -> str:
        return self.identity.worker_id

    @property
    def role(self) -> LeaderRole:
        return self.state.role

    @property
    def is_leader(self) -> bool:
        return self.state.role == LeaderRole.LEADER

    async def acquire_leadership(self) -> bool:
        """Attempt to acquire the exclusive leader lock."""
        try:
            acquired = await self.redis_client.set(
                self.lock_key,
                self.worker_id,
                nx=True,
                ex=self.lock_ttl,
            )
            if acquired:
                self.state.role = LeaderRole.LEADER
                logger.info(
                    f"👑 [SchedulerCoordinator] Worker {self.worker_id} acquired LEADER lock."
                )
                return True
            else:
                self.state.role = LeaderRole.STANDBY
                logger.info(
                    f"🛡️ [SchedulerCoordinator] Worker {self.worker_id} is in STANDBY mode (Leader lock held by another worker)."
                )
                return False
        except Exception as e:
            logger.warning(
                f"⚠️ [SchedulerCoordinator] Error connecting to Redis during acquire: {e}"
            )
            self.state.role = LeaderRole.STANDBY
            return False

    async def release_leadership(self) -> bool:
        """Safely release the leader lock using Lua script."""
        if not self.is_leader:
            return False

        try:
            result = await self.redis_client.eval(
                RELEASE_LOCK_LUA_SCRIPT,
                1,
                self.lock_key,
                self.worker_id,
            )
            self.state.role = LeaderRole.STANDBY
            if result == 1:
                logger.info(
                    f"🔓 [SchedulerCoordinator] Worker {self.worker_id} released LEADER lock."
                )
                return True
            return False
        except Exception as e:
            logger.warning(
                f"⚠️ [SchedulerCoordinator] Error releasing Redis leader lock: {e}"
            )
            self.state.role = LeaderRole.STANDBY
            return False

    async def _renew_leadership(self) -> bool:
        """Renew lock TTL using Lua script."""
        try:
            result = await self.redis_client.eval(
                RENEW_LOCK_LUA_SCRIPT,
                1,
                self.lock_key,
                self.worker_id,
                self.lock_ttl,
            )
            return result == 1
        except Exception as e:
            logger.warning(
                f"⚠️ [SchedulerCoordinator] Error renewing Redis lock TTL: {e}"
            )
            return False

    async def _heartbeat_loop(self) -> None:
        """Background task for leader: renew lock TTL every heartbeat_interval seconds."""
        logger.debug(
            f"💓 [SchedulerCoordinator] Starting heartbeat loop for leader {self.worker_id}"
        )
        while self.state.is_running and self.is_leader:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                if not self.state.is_running or not self.is_leader:
                    break

                renewed = await self._renew_leadership()
                if not renewed:
                    logger.warning(
                        f"⚠️ [SchedulerCoordinator] Leader {self.worker_id} lost lock ownership! Demoting to STANDBY..."
                    )
                    from app.core.scheduler import shutdown_scheduler

                    await shutdown_scheduler()
                    self.state.role = LeaderRole.STANDBY
                    # Switch to standby polling
                    if self.state.is_running:
                        self.state.standby_task = asyncio.create_task(
                            self._standby_poll_loop()
                        )
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    f"⚠️ [SchedulerCoordinator] Unexpected error in heartbeat loop: {e}"
                )

    async def _standby_poll_loop(self) -> None:
        """Background task for standby workers: periodically check if leader lock is available."""
        logger.debug(
            f"👀 [SchedulerCoordinator] Starting standby polling loop for {self.worker_id}"
        )
        while self.state.is_running and not self.is_leader:
            try:
                await asyncio.sleep(self.standby_poll_interval)
                if not self.state.is_running or self.is_leader:
                    break

                acquired = await self.acquire_leadership()
                if acquired:
                    logger.info(
                        f"👑 [SchedulerCoordinator] Worker {self.worker_id} successfully promoted to LEADER! Starting scheduler..."
                    )
                    from app.core.scheduler import start_scheduler

                    await start_scheduler(self.dishka_container)
                    self.state.heartbeat_task = asyncio.create_task(
                        self._heartbeat_loop()
                    )
                    break
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(
                    f"⚠️ [SchedulerCoordinator] Unexpected error in standby poll loop: {e}"
                )

    async def start(self) -> None:
        """Start coordination: acquire lock or start standby polling."""
        self.state.is_running = True
        acquired = await self.acquire_leadership()

        if acquired:
            from app.core.scheduler import start_scheduler

            await start_scheduler(self.dishka_container)
            self.state.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        else:
            self.state.standby_task = asyncio.create_task(self._standby_poll_loop())

    async def stop(self) -> None:
        """Stop coordinator, cancel tasks, shut down scheduler, and release lock."""
        logger.info(f"🛑 [SchedulerCoordinator] Stopping worker {self.worker_id}...")
        self.state.is_running = False

        if self.state.heartbeat_task and not self.state.heartbeat_task.done():
            self.state.heartbeat_task.cancel()
        if self.state.standby_task and not self.state.standby_task.done():
            self.state.standby_task.cancel()

        if self.is_leader:
            from app.core.scheduler import shutdown_scheduler

            await shutdown_scheduler()
            await self.release_leadership()
