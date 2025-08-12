from typing import Annotated, Optional

from redis.asyncio.client import Redis
from db.database import dbq
from db.database import db as get_db
from db.database import DbQuery
from dbm.redis_db import rdb
from fastapi import Depends
from lib.domain.buy.payment import Payment


class TsPayment(Payment):
    """implementation of Payment base class for testing purposes"""
    def __init__(
        self,
        db: Annotated[DbQuery, Depends(get_db)] = None,
        rdb: Annotated[Redis, Depends(rdb)] = None,
        ip: str = "127.0.0.1",
        lang: str = "en",
        coupon: Optional[str] = None,
        email: Optional[str] = None,
        plan: Optional[str] = None,
        permanent: Optional[str] = None,
        currency: Optional[str] = None,
    ):
        self.db = db
        self.rdb = rdb
        self.ip = ip
        self.lang = lang
        self.coupon = coupon
        self.email = email
        self.plan = plan
        self.permanent = permanent
        self.currency = currency
        self.trans = None

    async def confirmation():
        return
