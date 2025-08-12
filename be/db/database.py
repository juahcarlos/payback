from dbm.database import DbQueryMixin
from dbm.db_main import DbMain
from dbm.models import Coupons, Transactions, Users
from dbm.schemas import UserId

from db.models import TariffsWh
from db.schemas import Count, Partner, TariffsWhPd
from sqlalchemy import delete, func, select, update

from libs.logs import log


class DbQuery(DbMain, DbQueryMixin):
    """
    Database query class combining main DB engine and query mixin
    to perform specific data retrieval and update operations.
    """

    # gets

    async def get_partner(self, partner_id: int) -> Partner:
        """
        Get partner data by partner ID.

        Args:
            partner_id (int): Partner unique identifier.

        Returns:
            Partner | None: Partner data object or None if not found.
        """
        statement = select(Partners).where(Partners.id == partner_id)
        self.data_class = Partner
        result_ = await self.result_one(statement)
        return result_


    async def get_tariff(self, plan: int) -> TariffsWhPd:
        """
        Get tariff details by plan identifier.

        Args:
            plan (Any): Plan identifier, usually string or number.

        Returns:
            TariffsWhPd | None: Tariff data or None if not found.
        """
        statement = select(TariffsWh).where(TariffsWh.date == str(plan))
        self.data_class = TariffsWhPd
        result_ = await self.result_one(statement)
        return result_

    # updates

    async def update_coupon_times_used(self, coupon: str) -> None:
        """
        Increment the usage count of a coupon if it exists.

        Args:
            coupon (str): Coupon code string.
        """
        coupon_db = await self.get_coupon(coupon)
        if coupon_db is not None:
            statement = (
                update(Coupons)
                .where(Coupons.coupon == coupon)
                .values(times_used=coupon_db.times_used + 1)
            )
            await self.result(statement)

    async def update_user_full_finish(self, user: UserId) -> None:
        """
        Update user subscription and related info upon completion.

        Args:
            user (UserFull): User data object with updated info.
        """
        statement = (
            update(Users)
            .where(Users.email == user.email)
            .values(
                plan=user.plan,
                code=user.code,
                coupon=user.coupon,
                expires=user.expires,
                trial=user.trial,
            )
        )
        await self.result(statement)


dbq = DbQuery()


async def db():
    db = DbQuery()
    return db
