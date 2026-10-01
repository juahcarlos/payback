import json
from dataclasses import asdict

from fastapi import Depends
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import get_redis
from app.domain.tariffs import TariffReadModel
from app.repositories import TariffDBRepo, get_tariff_repo


class TariffService:
    def __init__(self, repo: TariffDBRepo, redis: Redis) -> None:
        self.repo = repo
        self.redis = redis

        self.redis_tariffs_key = "tariffs_whox" if settings.prod else "tariffs_whox_stage"
        self.redis_tariffs_ttl = 20

    async def _get_tariffs_from_redis(self) -> list[TariffReadModel] | None:
        str_data = await self.redis.get(self.redis_tariffs_key)
        if not str_data:
            return None

        data = json.loads(str_data)
        return [TariffReadModel(**d) for d in data]

    async def _write_tariffs_to_redis(self, str_data: str) -> None:
        await self.redis.set(self.redis_tariffs_key, str_data)
        await self.redis.expire(self.redis_tariffs_key, self.redis_tariffs_ttl)

    async def get_tariffs(self) -> list[TariffReadModel]:
        tariffs_list = await self._get_tariffs_from_redis()
        if not tariffs_list:
            tariffs_list = await self.repo.get_tariffs()
            str_data = json.dumps([asdict(tariff_data) for tariff_data in tariffs_list])
            await self._write_tariffs_to_redis(str_data)

        return tariffs_list


def get_tariff_service(
        repo: TariffDBRepo = Depends(get_tariff_repo),  # noqa: B008
        redis: Redis = Depends(get_redis),  # noqa: B008
) -> TariffService:
    return TariffService(repo, redis)
