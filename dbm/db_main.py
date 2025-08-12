import json
from typing import List, Optional

from grpclib.client import Channel
from pydantic import BaseModel
from sqlalchemy.dialects import mysql
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import ClauseElement, Executable

from config import settings
from grpc_lib import TestStub


async def request(data: str) -> str:
    """
    Sends a SQL query string via gRPC to the database service and
    returns the JSON-formatted response as a string.

    Args:
        data (str): SQL query string to execute.

    Returns:
        str: JSON-formatted string with the results of the executed
            SQL query.
    """
    async with Channel(host=settings.GRPC_HOST, port=settings.GRPC_PORT) as channel:
        stub = TestStub(channel)
        response = await stub.test(test=data)
        return response.test_res


class DbMain:
    """
    Convert SQL Alchemy statement to plain SQL query text ,
    send it to database service, where the query will be executed,
    receive result, wrap it to dataclass and return
    """

    def __init__(self) -> None:
        """
        Initializes the asynchronous database engine and sets
        the data_class attribute for parsing query results.
        """
        self.engine_ = create_async_engine(
            "mysql+aiomysql://",
        )
        self.data_class = None

    def sql_text_(
        self,
        statement: ClauseElement | Executable,
    ) -> str:
        """
        Converts a SQLAlchemy statement into its SQL string form.

        Args:
            statement (ClauseElement | Executable): SQLAlchemy
                statement.

        Returns:
            str: The SQL query as a string.
        """
        compiled = statement.compile(
            dialect=mysql.dialect(), compile_kwargs={"literal_binds": True}
        )
        try:
            text = str(compiled) % compiled.params
            return text
        except Exception as ex:
            print("ex", ex)

    async def query(
        self,
        statement: ClauseElement | Executable,
    ) -> str:
        """
        Converts a SQLAlchemy statement to raw SQL text using the
        sql_text_() method, sends it to a function that requests an
        external database service which connects to the DB, executes
        the query, and returns the result as JSON-formatted text.

        Args:
            statement (ClauseElement | Executable): SQL statement.

        Returns:
            str: JSON-formatted string response from the external
                database service.
        """
        query_ = self.sql_text_(statement)
        return await request(query_)

    async def result(
        self,
        statement: ClauseElement | Executable,
    ) -> Optional[List[BaseModel]]:
        """
        Sends a SQLAlchemy statement to convert it to text and send
        it to an external DB service to execute and get the result.

        Args:
            statement (ClauseElement | Executable): SQL statement.

        Returns:
            Optional[List[BaseModel]]: List of parsed data_class
                instances, or None if empty.
        """
        res = await self.query(statement)
        return await self.result_list(res)

    async def result_insert(
        self,
        statement: ClauseElement | Executable,
    ) -> BaseModel | None:
        """
        Converts an insert SQLAlchemy statement to raw SQL text, sends it
        to the external database service for execution, and returns the
        result.

        Args:
            statement (ClauseElement | Executable): SQL insert statement.

        Returns:
            BaseModel | None: Parsed result returned by the insert operation
                if the statement includes RETURNING; otherwise None.

        Raises:
            Exception: If the external service reports an error or
                the insert operation fails.
        """
        res = await self.query(statement)
        return res

    async def result_list(
        self,
        res: str,
    ) -> Optional[List[BaseModel]]:
        """
        Parses a JSON string into a list of data_class instances.

        Args:
            res (str): JSON string of records.

        Returns:
            Optional[List[BaseModel]]: List of parsed data_class
                instances, or an empty list.
        """
        result_ = []
        if len(res) > 0:
            result_ = [self.data_class(**r) for r in json.loads(res)]
        return result_

    async def result_one(
        self,
        statement: ClauseElement | Executable,
    ) -> Optional[BaseModel]:
        """
        Sends a query and returns the first parsed data_class instance
        from the query results list or None if no results.

        Args:
            statement (ClauseElement | Executable): SQL statement.

        Returns:
            Optional[BaseModel]: First parsed data_class instance or None.
        """
        res = await self.query(statement)
        result_list = await self.result_list(res)
        if len(result_list) > 0:
            return result_list[0]
