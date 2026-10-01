from dataclasses import asdict

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.coupons import (
    CouponReadModel,
    CouponSaveModel,
)
from app.models import Coupons

from .base import BaseDBRepo


class CouponDBRepo(BaseDBRepo):

    # CREATE

    async def insert_coupon(self, coupon_data: CouponSaveModel) -> None:
        statement = insert(Coupons).values(**asdict(coupon_data))
        await self.insert_only(statement)

    # READ

    async def get_coupon_by_code(self, coupon_code: str) -> CouponReadModel | None:
        statement = select(Coupons).where(Coupons.coupon == coupon_code)
        return await self.select_one(statement, CouponReadModel)

    async def get_coupon_by_code_in_session(
            self,
            session: AsyncSession,
            coupon_code: str,
    ) -> Coupons | None:
        statement = select(Coupons).where(Coupons.coupon == coupon_code)
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    # UPDATE

    async def update_coupon_times_used(self, coupon_code: str) -> None:
        statement = (
            update(Coupons)
            .where(Coupons.coupon == coupon_code)
            .values(times_used=Coupons.times_used + 1)
        )
        await self.update_only(statement)

    async def increment_coupon_times_used(
            self,
            session: AsyncSession,
            coupon_code: str,
    ) -> None:
        statement = (
            update(Coupons)
            .where(Coupons.coupon == coupon_code)
            .values(times_used=Coupons.times_used + 1)
        )
        await session.execute(statement)


def get_coupon_repo() -> CouponDBRepo:
    return CouponDBRepo()
