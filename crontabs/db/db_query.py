from datetime import datetime, timedelta
from typing import List

from sqlalchemy import delete, insert, select, update
from sqlalchemy.sql import and_

from crontabs.db.schemas import CustomerPromo
from dbm.database import DbQuery as DBQ
from dbm.database import DbQueryMixin
from dbm.db_main import DbMain
from dbm.models import Coupons, Transactions, Users
from dbm.schemas import CouponsPd, UserId


class DbQuery(DBQ, DbMain, DbQueryMixin):
    async def get_user_db(self, email: str) -> UserId:
        """Select user by email (unique)"""
        statement = select(Users).where(Users.email == email)
        self.data_class = UserId
        result_ = await self.result_one(statement)
        return result_

    async def get_all_users_reminder(self) -> List[UserId]:
        """
        Select users whose tariff expired within the range
        from 2 days ago up to 1 day from now.
        """
        statement = select(Users).where(
            Users.expires.between(
                int(datetime.now().strftime("%s")) - 86400 * 2,
                int(datetime.now().strftime("%s")) + 86400,
            )
        )
        self.data_class = UserId
        result_ = await self.result(statement)
        return result_

    async def get_customer_promo_db(self) -> List[CustomerPromo]:
        """
        Queries users emails from transactions that:
        - expire within a one-hour window exactly 7 days forward from now,
        - have a duration of 30 days,
        - are non-trial subscriptions,
        - and are completed transactions.
        """
        statement = select(
            Users.email.label("address"),
            Users.lang,
        ).where(
            Users.email.in_(
                select(Transactions.email)
                .with_hint(Transactions, "USE INDEX(transactions_expires)")
                .where(
                    and_(
                        Transactions.expires.between(
                            datetime.now() + timedelta(days=7) - timedelta(hours=1),
                            datetime.now() + timedelta(days=7),
                        ),
                        Transactions.days == 30,
                        Transactions.trial.is_(False),
                        Transactions.complete.is_(True),
                    )
                )
            )
        )
        self.data_class = CustomerPromo
        result_ = await self.result(statement)
        return result_

    async def get_customer_coupon_db(self) -> List[CustomerPromo]:
        """Selects users who completed a 30-day trial transaction
        exactly one day ago within a one-hour window."""
        statement = (
            select(
                Users.email.label("address"),
                Users.lang,
            )
            .join(Transactions, Transactions.email == Users.email)
            .where(
                and_(
                    Transactions.created.between(
                        (datetime.now() - timedelta(days=1)) - timedelta(hours=1),
                        datetime.now() - timedelta(days=1),
                    ),
                    Transactions.days == 30,
                    Transactions.trial.is_(True),
                    Transactions.complete.is_(True),
                )
            )
        )
        self.data_class = CustomerPromo
        result_ = await self.result(statement)
        return result_

        # -------- create ---------

    async def insert_coupon(self, data: CouponsPd) -> None:
        """Insert new coupon in DB"""
        statement = insert(Coupons).values(
            coupon=data.coupon,
            percent=data.percent,
            created=data.created,
            expiration=data.expiration,
            plans=data.plans,
        )
        await self.result(statement)

    # -------- update --------

    async def update_user_after_insert(self, user: UserId) -> None:
        """update cn column by user.id combined with prefix 'sec"""
        statement = (
            update(Users).where(Users.email == user.email).values(cn=f"sec{user.id}")
        )
        await self.result(statement)

    async def delete_user(self, email: str) -> None:
        """Delete user by email"""
        statement = delete(Users).where(Users.email == email)
        await self.result(statement)


dbq = DbQuery()
