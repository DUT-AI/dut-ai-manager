from loguru import logger
from redis.asyncio import ConnectionPool, Redis

from app.core.config import settings


def create_redis_pool(url: str | None = None) -> ConnectionPool:
    """Create an asynchronous Redis connection pool."""
    redis_url = url or settings.REDIS_URL
    return ConnectionPool.from_url(
        redis_url,
        max_connections=20,
        decode_responses=True,
    )


def create_redis_client(pool: ConnectionPool | None = None) -> Redis:
    """Create an asynchronous Redis client instance from a pool or default url."""
    if pool is not None:
        return Redis(connection_pool=pool)
    return Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
    )


async def close_redis_client(client: Redis) -> None:
    """Close the Redis client connection gracefully."""
    try:
        await client.aclose()
        logger.debug("🔌 Redis client connection closed")
    except Exception as e:
        logger.warning(f"⚠️ Error closing Redis client: {e}")
