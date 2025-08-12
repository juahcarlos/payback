"""
Creates and returns an asynchronous Redis client.
Returns:
    Redis: An async Redis client.
"""

from redis import asyncio as aioredis
from redis.asyncio.client import Redis

from config import settings

redis_stright: Redis = aioredis.from_url(
    settings.REDIS,
    encoding="utf-8",
    decode_responses=True,
    max_connections=2**31,
)


async def rdb() -> Redis:
    return redis_stright
