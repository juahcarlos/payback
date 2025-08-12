import hashlib
import re
from typing import Annotated

import httpx
from redis.asyncio.client import Redis
from config_be import settings
from dbm.redis_db import rdb
from db.schemas import TransactionFull
from fastapi import Depends

from be.db.schemas import FreekassaConfirmData
from libs.logs import log


async def usd_to_rub(rdb: Annotated[Redis, Depends(rdb)]):
    rate_cache = await rdb.get("usdtorub")

    if rate_cache is not None:
        rate = rate_cache.decode("utf-8")
        if rate != b"":
            rate = float(rate)
    else:
        async with httpx.AsyncClient() as client:
            try:
                response: httpx.Response = await client.get(
                    "https://www.cbr-xml-daily.ru/daily_json.js",
                    timeout=60,
                )
                response.raise_for_status()
                rates = response.json()
                rate = float(rates["Valute"]["USD"]["Value"])
                await rdb.set("usdtorub", rate)
                await rdb.expire("usdtorub", 6)
            except httpx.HTTPError as e:
                rate = 80
                raise RuntimeError(f"Request failed: {e}")

    return rate


def sign_confirm_freekassa(data: str) -> str:
    hash_string = ":".join(
        (
            settings.FREEK_SHOP_ID,
            str(data.AMOUNT),
            settings.FREEK_SECRET_2,
            str(data.MERCHANT_ORDER_ID),
        )
    )
    sign = hashlib.md5(hash_string.encode("utf8")).hexdigest()

    return sign


async def verify(
    rdb,
    data: FreekassaConfirmData,
    trans: TransactionFull,
):
    if data.ip is None or (
        data.ip not in settings.FREEK_ALLOWED_HOSTS and not data.ip.startswith("192.")
    ):
        return f"Not allowed remote IP {data.ip}"
    if trans is None:
        return "transaction is None"
    if trans.complete == 1:
        return f"Already completed {trans.id}"
    if trans.email is None:
        return f"Invalid ID {trans.id}"
    if data.SIGN is None:
        return "Security hash is not in parameters"
    if str(data.MERCHANT_ID) != str(settings.FREEK_SHOP_ID):
        log.error(
            f"""data.MERCHANT_ID {data.MERCHANT_ID}
            settings.FREEK_SHOP_ID {settings.FREEK_SHOP_ID}"""
        )
        return f"Invalid account {data.MERCHANT_ID}"
    data.AMOUNT = re.sub(r"(\d+)\.0+", r"\1", str(data.AMOUNT))
    trans.amount = re.sub(r"(\d+)\.0+", r"\1", str(trans.amount))

    usdtorub = await usd_to_rub(rdb)

    if (
        str(data.AMOUNT) != str(trans.amount)
        and abs(float(data.AMOUNT) - float(trans.amount) * usdtorub) > 300
    ):
        return f"Invalid amount {data.AMOUNT} {trans.amount}"

    sign = sign_confirm_freekassa(data)

    if sign != data.SIGN:
        return f"Invalid hash sum {data.SIGN}"
    return 1
