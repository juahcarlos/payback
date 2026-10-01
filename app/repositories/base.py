from typing import Any, TypeVar, cast

from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession

from app.core.database import create_session as new_session
from app.domain.base import BaseDomainModel


T = TypeVar("T", bound=BaseDomainModel)


class BaseDBRepo:
    async def _perform_request(
            self,
            statement,
            with_result: bool = False,
    ) -> list[dict[str, Any]] | None:
        async with new_session() as session:
            async with session.begin():
                result = await session.execute(statement)
                if not with_result:
                    return None
                return [self._row_to_dict(row) for row in result.mappings()]

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        values = dict(row)
        if len(values) == 1:
            value = next(iter(values.values()))
            if hasattr(value, "__table__"):
                return {
                    column.key: getattr(value, column.key)
                    for column in value.__table__.columns
                }
        return values

    def create_session(self, bind: AsyncConnection | None = None) -> AsyncSession:
        return new_session(bind=bind)

    async def select_one(
            self,
            statement,
            entity: type[T],
    ) -> T | None:
        data_list = await self._perform_request(statement, with_result=True)
        if data_list:
            return entity(**data_list[0])

        return None

    async def select_many(
            self,
            statement,
            entity: type[T],
    ) -> list[T]:
        data_list = await self._perform_request(statement, with_result=True)
        result = []
        if data_list:
            result = [entity(**obj) for obj in data_list]

        return result

    async def insert_only(self, statement) -> None:
        await self._perform_request(statement)

    async def insert_with_primary_key(self, statement) -> int:
        async with new_session() as session:
            async with session.begin():
                result = cast(CursorResult[Any], await session.execute(statement))
                primary_key = result.inserted_primary_key[0]
                if primary_key is None:
                    raise RuntimeError("INSERT did not return a primary key")
                return int(primary_key)

    async def insert_with_result(
            self,
            statement,
            entity: type[T],
    ) -> T | None:
        data_list = await self._perform_request(statement, with_result=True)
        if data_list:
            return entity(**data_list[0])

        return None

    async def update_only(self, statement) -> None:
        await self._perform_request(statement)

    async def delete(self, statement) -> None:
        await self._perform_request(statement)
