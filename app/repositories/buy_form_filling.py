from dataclasses import asdict

from sqlalchemy import delete, insert, select, update

from app.domain.buy_form_filling import (
    BuyFormFillingReadModel,
    BuyFormFillingSaveModel,
)
from app.models import BuyFormFilling
from app.utils.email import normalize_email

from .base import BaseDBRepo


class BuyFormFillingDBRepo(BaseDBRepo):

    # CREATE

    async def insert_filling(
            self,
            form_data: BuyFormFillingSaveModel,
    ) -> BuyFormFillingReadModel | None:
        values = asdict(form_data)
        if values["email"] is not None:
            values["email"] = normalize_email(values["email"])
        statement = insert(BuyFormFilling).values(**values)
        await self.insert_only(statement)
        return await self.get_filling_by_max_id()

    # READ

    async def get_filling_by_id(self, filling_id: int) -> BuyFormFillingReadModel | None:
        statement = select(BuyFormFilling).where(BuyFormFilling.id == filling_id)
        return await self.select_one(statement, BuyFormFillingReadModel)

    async def get_filling_by_max_id(self) -> BuyFormFillingReadModel | None:
        statement = select(BuyFormFilling).order_by(BuyFormFilling.id).limit(1)
        return await self.select_one(statement, BuyFormFillingReadModel)

    # UPDATE

    async def update_filling(self, filling_id: int, email: str) -> None:
        statement = (
            update(BuyFormFilling)
            .where(BuyFormFilling.id == filling_id)
            .values(email=normalize_email(email))
        )
        await self.update_only(statement)

    # DELETE

    async def delete_filling(self, filling_id: int) -> None:
        statement = delete(BuyFormFilling).where(BuyFormFilling.id == filling_id)
        await self.delete(statement)


def get_buy_form_filling_repo() -> BuyFormFillingDBRepo:
    return BuyFormFillingDBRepo()
