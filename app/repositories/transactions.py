from dataclasses import asdict
from datetime import datetime

from sqlalchemy import insert, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.domain.transactions import (
    TransactionReadModel,
    TransactionSaveModel,
    TransactionsCountModel,
)
from app.models import Transactions
from app.utils.email import normalize_email

from .base import BaseDBRepo


class TransactionDBRepo(BaseDBRepo):

    # CREATE

    async def insert_transaction(
            self,
            transaction_data: TransactionSaveModel,
    ) -> int:
        values = asdict(transaction_data)
        values["email"] = normalize_email(transaction_data.email)
        statement = insert(Transactions).values(**values)
        return await self.insert_with_primary_key(statement)

    # READ

    async def get_transaction_by_id(self, transaction_id: int) -> TransactionReadModel | None:
        statement = select(Transactions).where(Transactions.id == transaction_id)
        return await self.select_one(statement, TransactionReadModel)

    async def get_transaction_for_update(
            self,
            session: AsyncSession,
            transaction_id: int,
    ) -> Transactions | None:
        statement = (
            select(Transactions)
            .where(Transactions.id == transaction_id)
            .with_for_update()
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_transaction_by_user_email(
            self,
            user_email: str,
    ) -> TransactionReadModel | None:
        user_email = normalize_email(user_email)
        statement = (
            select(Transactions)
            .where(Transactions.email == user_email)
            .order_by(Transactions.id.desc())
            .limit(1)
        )
        return await self.select_one(statement, TransactionReadModel)

    async def get_transactions_count_by_email(self, user_email: str) -> TransactionsCountModel | None:
        user_email = normalize_email(user_email)
        statement = (
            select(func.count(Transactions.id).label("count"))
            .where(Transactions.email == user_email)
        )
        return await self.select_one(statement, TransactionsCountModel)

    # UPDATE

    async def update_transaction_complete(self, transaction_id: int) -> None:
        statement = (
            update(Transactions)
            .where(Transactions.id == transaction_id)
            .values(complete=1)
        )
        await self.update_only(statement)

    async def update_transaction_expires(self, transaction_id: int, expires: datetime) -> None:
        statement = (
            update(Transactions)
            .where(Transactions.id == transaction_id)
            .values(expires=expires)
        )
        await self.update_only(statement)



def get_transaction_repo() -> TransactionDBRepo:
    return TransactionDBRepo()
