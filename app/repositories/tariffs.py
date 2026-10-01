from sqlalchemy import select

from app.domain.tariffs import TariffReadModel
from app.models import TariffsWhox

from .base import BaseDBRepo


class TariffDBRepo(BaseDBRepo):

    # READ

    async def get_tariffs(self) -> list[TariffReadModel]:
        statement = select(TariffsWhox)
        return await self.select_many(statement, TariffReadModel)

    async def get_tariff_by_plan(self, plan: str) -> TariffReadModel | None:
        statement = select(TariffsWhox).where(TariffsWhox.date == str(plan))
        return await self.select_one(statement, TariffReadModel)


def get_tariff_repo() -> TariffDBRepo:
    return TariffDBRepo()
