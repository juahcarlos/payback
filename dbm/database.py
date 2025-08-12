from sqlalchemy import delete, insert, select, update

from dbm.db_main import DbMain
from dbm.models import Coupons, Transactions, Users
from dbm.schemas import CouponsPd, TransactionFull, User, UserId


class DbQueryMixin:
    async def get_coupon(self, coupon: str) -> CouponsPd:
        """
        Get a coupon record by its coupon code.

        Args:
            coupon (str): Coupon code.

        Returns:
            CouponsPd: Parsed coupon data object, or None if not found.
        """
        statement = select(Coupons).where(Coupons.coupon == coupon)
        self.data_class = CouponsPd
        result_ = await self.result_one(statement)
        return result_

    async def get_trans_by_id(self, trans_id: int) -> TransactionFull:
        """
        Get a transaction record by its ID.

        Args:
            trans_id (int): Transaction ID.

        Returns:
            TransactionFull: Parsed transaction data object, or None if not found.
        """
        statement = select(Transactions).where(Transactions.id == trans_id)
        self.data_class = TransactionFull
        result_ = await self.result_one(statement)
        return result_

    async def get_trans_by_email(self, email: str) -> TransactionFull:
        """
        Get the most recent transaction for the given email.

        Args:
            email (str): Email address.

        Returns:
            TransactionFull: Parsed transaction data object, or None if not found.
        """
        statement = (
            select(Transactions)
            .where(Transactions.email == email)
            .order_by(Transactions.id.desc())
            .limit(1)
        )
        self.data_class = TransactionFull
        result_ = await self.result_one(statement)
        return result_

    async def get_user_by_email(self, email: str) -> UserId:
        """
        Get a user record by email (case-insensitive).

        Args:
            email (str): Email address.

        Returns:
            UserId: Parsed user ID data object, or None if not found.
        """
        email = email.lower()
        statement = select(Users).where(Users.email == email)
        self.data_class = UserId
        result_ = await self.result_one(statement)
        return result_

    async def update_trans_complete(self, trans_id: int) -> None:
        """
        Mark a transaction as complete by setting its 'complete' field to 1.

        Args:
            trans_id (int): Transaction ID.

        Returns:
            None
        """
        statement = (
            update(Transactions).where(Transactions.id == trans_id).values(complete=1)
        )
        await self.result(statement)

    async def update_trans_expires(self, expires: int, trans_id: int) -> None:
        """
        Update the 'expires' field of a transaction.

        Args:
            expires (int): New expiration value.
            trans_id (int): Transaction ID.

        Returns:
            None
        """
        statement = (
            update(Transactions)
            .where(Transactions.id == trans_id)
            .values(expires=expires)
        )
        await self.result(statement)

    async def insert_email(self, user: User) -> None:
        """
        Insert a new user record into the database.

        Args:
            user (User): User data object.

        Returns:
            None
        """
        statement = insert(Users).values(
            email=user.email,
            code=user.code,
            created=user.created,
            expires=user.expires,
            password=user.password,
            reg_source=user.reg_source,
            version_page=user.version_page,
            country_iso=user.country_iso,
            lang=user.lang,
            dubious=0,
            subscribed=0,
            plan=user.plan,
            trial=user.trial,
        )
        await self.result_insert(statement)

    async def insert_transaction(self, data: TransactionFull) -> TransactionFull:
        """
        Insert a new transaction record and return the most recent transaction
        for the given email.

        Args:
            data (TransactionFull): Transaction data object.

        Returns:
            TransactionFull: Most recent transaction for the email.
        """
        statement = insert(Transactions).values(
            system=data.system,
            data=data.data,
            days=data.days,
            amount=data.amount,
            email=data.email,
            created=data.created,
            expires=data.expires,
            trial=data.trial,
            coupon=data.coupon,
            version_page=data.version_page,
            country_iso=data.country_iso,
            complete=data.complete,
            partner_referrer_id=data.partner_referrer_id,
            check_order_id=data.check_order_id,
            refund=data.refund,
        )
        await self.result_insert(statement)
        result = await self.get_trans_by_email(data.email)
        return result

    async def delete_trans_by_id(self, id: int) -> None:
        """
        Delete a transaction record by ID.

        Args:
            id (int): Transaction ID.

        Returns:
            None
        """
        statement = delete(Transactions).where(Transactions.id == id)
        await self.result(statement)

    async def delete_user(self, email: str) -> None:
        """
        Delete a user record by email.

        Args:
            email (str): Email address.

        Returns:
            None
        """
        statement = delete(Users).where(Users.email == email)
        await self.result(statement)


class DbQuery(DbMain, DbQueryMixin):
    ...


dbq = DbQuery()


async def db():
    db = DbQuery()
    return db
