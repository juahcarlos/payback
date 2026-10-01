from sqlalchemy import select

from app.domain.partners import PartnerReadModel
from app.models import Partners

from .base import BaseDBRepo


class PartnerDBRepo(BaseDBRepo):

    # READ

    async def get_partner_by_id(self, partner_id: int) -> PartnerReadModel | None:
        statement = select(Partners).where(Partners.id == partner_id)
        return await self.select_one(statement, PartnerReadModel)


def get_partner_repo() -> PartnerDBRepo:
    return PartnerDBRepo()
