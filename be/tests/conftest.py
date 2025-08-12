import hashlib
import socket
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, List

from redis import asyncio as aioredis
import httpx
import pytest
import pytest_asyncio
from redis.asyncio.client import Redis
from config_be import settings
from db.database import DbQuery
from db.database import dbq as db
from db.schemas import FreekassaConfirmData, PaymentContext
from dbm.database import TransactionFull, User
from fastapi import Request
from lib.domain.buy.freekassa import Freekassa
from tests.test_cls import TsPayment

sys.path.append(str(Path(__file__).parents[1]))


@pytest_asyncio.fixture()
async def request_emulated():
    """Static freezed real Fastapi request to mock the tests"""
    scope = {
      "type": "http",
      "asgi": {
        "version": "3.0",
        "spec_version": "2.3"
      },
      "http_version": "1.1",
      "server": ("127.0.0.1", 8093),
      "client": ("45.9.46.177", 65132),
      "scheme": "http",
      "method": "GET",
      "root_path": "",
      "query_string": (b"email=avikouganb10%40ggmail.com&plan=30&hidden_captcha="
        b"5765eb4adaa292b68943c43dcf552a90f4e2392373cd288d1730740dd492a59b"),
      "headers": [
        (b"host", b"127.0.0.1:8093"),
        (b"connection", b"keep-alive"),
        (b"cache-control", b"max-age=0"),
        (b"upgrade-insecure-requests", b"1"),
        (b"user-agent",
        b"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        b"(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 OPR/114.0.0.0"),
        (b"accept",
        b"text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
        b"image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7"),
        (b"accept-encoding", b"gzip, deflate"),
        (b"accept-language", b"en-US,en;q=0.9"),
        (b"cookie",
        b"SLG_G_WPT_TO=ru; SLG_GWPT_Show_Hide_tmp=1; SLG_wptGlobTipTmp=1; "
        b"SLO_GWPT_Show_Hide_tmp=0; SLO_wptGlobTipTmp=0; user='"
        b"gAAAAABnNIWHX2RVpTjPBCP5C4O8l66VOdtD0KWGRv4_jADbT8RhET-yuhwL2eu8"
        b"D40oAvQueYvxb0IGPnKy8F-8y0MwxrzqDvtEkD9bJpOaIEg_GXpRHVo='"),
      ],
        "state": {},
        "path_params": {"lang": "en"}
    }
    return Request(scope=scope)


@pytest_asyncio.fixture()
async def ctx() -> PaymentContext:
    """
    Payload context to create account and  initialize
    and create payment with one of outer payment systems
    """
    return PaymentContext(
        email=settings.TEST_EMAIL,
        coupon=None,
        plan=30,
        lang="en",
        ip="127.0.0.1",
        currency="freekassa",
    )


@pytest_asyncio.fixture()
async def ctx_trial() -> PaymentContext:
    """
    Payload context to create trial account
    """
    return PaymentContext(
        email=settings.TEST_EMAIL,
        coupon=None,
        plan=0,
        lang="en",
        ip="127.0.0.1",
        currency="free",
    )


@pytest_asyncio.fixture()
def local_ip() -> str:
    """Determining the local IP address usin python sucket lib"""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 1))  # connect() for UDP doesn't send packets
    ip = s.getsockname()[0]
    return ip


@pytest_asyncio.fixture()
async def rd() -> Redis:
    """create and return Redis handler"""
    redis_stright: Redis = aioredis.from_url(
        settings.REDIS,
        encoding="utf-8",
        decode_responses=True,
        max_connections=2 ** 31,
    )    
    return redis_stright


@pytest_asyncio.fixture()
async def test_payment(request_emulated: Request, rd: Redis) -> TsPayment:
    """Implement and initialise payment class to test creation payment"""
    test_payment = TsPayment(
        db,
        rd,
        "45.9.46.137 ",
        "en",
        "WELCOME",
        settings.TEST_EMAIL,
        30,
        False,
        "free",
    )
    return test_payment


@pytest_asyncio.fixture()
async def test_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """creates and yield client for http requests"""
    async with httpx.AsyncClient() as client:
        yield client


@pytest_asyncio.fixture()
async def args1(rd: Redis) -> List[DbQuery|Redis]:
    """Retur tuple of database and redis handlers""" 
    return (db, rd)


# fmt: off
@pytest_asyncio.fixture()
async def args2() -> List[int | str | bool]:
    """Return tuple of parameters to crate payment"""
    return (
        [
        "en", "FORBACK98", settings.TEST_EMAIL, 30,
        "5765eb4adaa292b68943c43dcf552a90f4e2392373cd288d1730740dd492a59b", False
        ]
    )
# fmt: on


@pytest_asyncio.fixture()
async def test_freekassa(
    request_emulated: Request, rd: Redis, args1: list, args2: list
) -> AsyncGenerator[Freekassa, None]:
    """
    Insert user and transaction to DB tables,
    yield Freekassa() object,
    delete just inserted user and transaction from DB
    """
    await db.delete_user(settings.TEST_EMAIL)

    user = User(
        email=settings.TEST_EMAIL,
        code=settings.TEST_CODE,
        trial=False,
        plan=settings.TEST_PLAN,
        expires=int((datetime.now() + timedelta(days=30)).strftime("%s")),
    )

    await db.insert_email(user)

    trans_data = TransactionFull(
        system="freekassa",
        days=30,
        amount=0.20,
        email=settings.TEST_EMAIL,
        created=datetime.now(),
        expires=datetime.now() + timedelta(days=2),
        trial=0,
        coupon="FORBACK",
        version_page=2,
        country_iso="us",
        complete=0,
        partner_referrer_id=0,
        check_order_id=0,
        refund=0,
    )
    trans_in_db_2 = await db.insert_transaction(trans_data)

    request = request_emulated
    request.scope["path"] = "/en/vpn/payment/create/freekassa"

    yield Freekassa(*args1)

    await db.delete_trans_by_id(trans_in_db_2.id)
    await db.delete_user(settings.TEST_EMAIL)


@pytest.fixture(scope="package")
def freekassa_confirm_data_mock() -> FreekassaConfirmData:
    """Return dataclass with Freekassa webhook data"""
    data = FreekassaConfirmData(
        MERCHANT_ORDER_ID=4467877,
        SIGN="invalid-hash",
        MERCHANT_ID=settings.FREEK_SHOP_ID,
        AMOUNT=20,
        ip="127.0.0.1",
    )

    hash_string = ":".join(
        (
            settings.FREEK_SHOP_ID,
            str(data.AMOUNT),
            settings.FREEK_SECRET_2,
            str(data.MERCHANT_ORDER_ID),
        )
    )

    data.SIGN = hashlib.md5(hash_string.encode("utf8")).hexdigest()

    return data


@pytest.fixture(scope="package")
def freekassa_confirm_trans_mock() -> TransactionFull:
    """Return data of transaction that supposed to be confirmed by webhook"""
    return TransactionFull(
        id=4467871,
        complete=0,
        email=settings.TEST_EMAIL,
        amount=20,
    )
