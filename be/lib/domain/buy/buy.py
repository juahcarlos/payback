import json
import re
from datetime import datetime
from typing import Annotated, Optional

from redis.asyncio.client import Redis
from config_be import settings
from db.database import DbQuery, db
from dbm.redis_db import rdb
from db.schemas import CouponCheck, TariffsWhPd
from fastapi import Depends
from fastapi.responses import Response
from lib.domain.buy.utils import encrypt_cookie_email

from libs.logs import log


async def tariffs(
    db: Annotated[DbQuery, Depends(db)],
    rdb: Annotated[Redis, Depends(rdb)],
) -> TariffsWhPd:
    """
    Retrieve tariffs data from Redis cache or database if cache miss.

    Args:
        db: Database handler to fetch tariffs.
        rdb: Redis client for caching.

    Returns:
        str: JSON string of tariffs data.
    """
    result = await rdb.get("tariffs_whox")

    if result is None:
        tariffs = await db.get_tariffs()
        result = json.dumps([t.model_dump() for t in tariffs])
        await rdb.set("tariffs_whox", result)
        await rdb.expire("tariffs_whox", 20)

    return result


async def check_coupon(
    db: Annotated[DbQuery, Depends(db)],
    coupon: str,
    tariff: Optional[str | None] = None,
):
    """
    Verify if coupon is valid and applicable.

    Args:
        db: Database handler for executing queries.
        coupon: Coupon ID string to identify the coupon in the database.
        tariff: Optional tariff name which the coupon applies to.

    Returns:
        int:
            - 1 if coupon is invalid or missing,
            - 0 if coupon format is incorrect, not found, not applicable, expired,
              or usage limit exceeded.
        dict: If valid, returns a dictionary with keys:
            - 'percent': int, discount percent,
            - 'prolong': int, prolongation period.
    """
    if not coupon or coupon == "" or coupon is None:
        return 1

    reg_search = re.search(r"^[a-zA-Z0-9]{3,20}$", coupon)
    if not reg_search:
        log.debug(f"coupon {coupon} has wrong format")
        return 0

    coupon_db = await db.get_coupon(coupon)
    if coupon_db is None:
        return 0

    if coupon_db.plans is not None and coupon_db.plans != "" and tariff is not None:
        plans = [int(pl) for pl in coupon_db.plans.split(",")]
        if int(tariff) not in plans:
            return 0

    if (
        coupon_db.times_used >= coupon_db.max_use_limit
        and coupon_db.max_use_limit != 0
        and coupon_db.max_use_limit is not None
    ):
        return 0

    if coupon_db.expiration < datetime.now():
        return 0

    result = CouponCheck(
        percent=coupon_db.percent,
        prolong=coupon_db.prolong,
    )

    return result.model_dump()
