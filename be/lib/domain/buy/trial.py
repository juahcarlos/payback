import json
from typing import Annotated

from redis.asyncio.client import Redis
from dbm.redis_db import rdb
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from lib.domain.buy.payment import Payment

from be.db.database import DbQuery, db
from be.db.schemas import PaymentContextTrial

env = Environment(loader=FileSystemLoader("templates"))


class PaymentTrial(Payment):
    def __init__(
        self,
        db: Annotated[DbQuery, Depends(db)],
        rdb: Annotated[Redis, Depends(rdb)],
    ):
        self.db = db
        self.rdb = rdb
        self.trans = None

    async def create(self, ctx: PaymentContextTrial) -> str:
        await super().create(ctx)

        result = json.dumps({"status": "OK"})
        return result

    async def confirmation(self):
        pass
