from redis.asyncio import Redis, from_url

from app.core.config import settings


class RedisClient:
    def __init__(self, url: str) -> None:
        self._url = url
        self._client: Redis | None = None

    async def connect(self) -> Redis:
        if self._client is None:
            self._client = from_url(
                self._url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=20,  # 2**31,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    async def get_client(self) -> Redis:
        return await self.connect()


redis_manager = RedisClient(settings.redis_url)


async def get_redis() -> Redis:
    return await redis_manager.get_client()
