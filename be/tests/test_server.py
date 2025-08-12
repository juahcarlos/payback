import hashlib
import json
from typing import Annotated

import pytest
from redis.asyncio.client import Redis
from config_be import settings
from db.database import dbq as db
from dbm.redis_db import rdb
from db.schemas import PaymentContext, TransactionFull
from fastapi import Depends
from fastapi.testclient import TestClient
from lib.domain.buy.buy import check_coupon
from lib.domain.buy.freekassa import Freekassa
from lib.domain.buy.freekassa_verify import verify
from lib.domain.buy.utils import (
    decrypt_cookie_email,
    encrypt_cookie_email
)
from tests.test_cls import TsPayment

headers = {"Accept": "application/json", "Content-Type": "application/json"}


async def request_by_kwargs(
    test_client: TestClient,
    method: str,
    path: str,
    **kwargs,
) -> None:
    """Make request to testing service using pytest TestClient"""
    request = test_client.build_request(
        method,
        settings.BASE_URL + path,
        headers=headers,
        content=kwargs.get("content"),
        params=kwargs.get("params"),
        timeout=60,
    )

    response = await test_client.send(request)
    assert response.status_code == 200
    return response


@pytest.mark.asyncio
async def test_check_coupon(test_client) -> None:
    """Test /payment/check_coupon endpoint"""
    params = "coupon=WELCOME&lang=en"
    res = await request_by_kwargs(
        test_client, "GET", "/vpn/payment/check_coupon", params=params
    )
    assert res.json() == 0 or res.json() == 10


@pytest.mark.asyncio
async def test_encrypt_cookie_email() -> None:
    """
    Test encrypting method to store email in cookie
    until the payment session will be completed.
    """
    res_encrypt = encrypt_cookie_email(settings.TEST_EMAIL)
    res_decrypt = decrypt_cookie_email(res_encrypt)
    assert res_decrypt == settings.TEST_EMAIL


@pytest.mark.asyncio
async def test_check_ip_in_time(
    test_payment: TsPayment,
    ctx: PaymentContext,
    rd: Annotated[Redis, Depends(rdb)],
) -> None:
    """Test checking repeated request from the same IP address method"""
    rediskey = "ip_count_" + test_payment.currency + ":" + test_payment.ip
    ip_amount = await rd.get(rediskey)
    res = await test_payment._check_ip_in_time(ctx)

    if ip_amount is not None:
        ip_amount = int(ip_amount)

    if ip_amount is None or ip_amount < 2:
        assert res is None
    else:
        assert res == 0


@pytest.mark.asyncio
async def test_check_already_sent(
    test_payment: TsPayment,
    ctx: PaymentContext,
    rd: Annotated[Redis, Depends(rdb)],
) -> None:
    """Test checking that access code is already sent to customer"""
    rkey = settings.TEST_EMAIL + ":trial"
    await rd.delete(rkey)
    await rd.set(rkey, 1, ex=20)

    with pytest.raises(Exception) as exc_info:
        await test_payment._check_already_sent(ctx)
        assert exc_info.value.name == "Access code allready sent"


@pytest.mark.asyncio
async def test_is_blacklisted_email_hosting(
    test_payment: TsPayment,
    ctx: PaymentContext,
) -> None:
    """Test checking if email is in blacklist"""
    test_payment.email = "aadfa@xoxy.uk"
    ctx.email = "aadfa@xoxy.uk"

    with pytest.raises(Exception) as exc_info:
        await test_payment._is_blacklisted_email_hosting(ctx)

    assert "Using this email hosting is not allowed" in exc_info.value.name


@pytest.mark.asyncio
async def test_fix_email(test_payment: TsPayment, ctx: PaymentContext) -> None:
    """Test fixing email domain method"""
    test_payment.email = "aadfa@bmail.com"
    ctx.email = "aadfa@bmail.com"
    with pytest.raises(Exception) as exc_info:
        await test_payment._fix_email(ctx)
        assert "Using this email hosting is not allowed" in exc_info.value.name
    assert ctx.email == "aadfa@gmail.com"


@pytest.mark.asyncio
async def test_create_freekassa(
    test_freekassa: Freekassa,
    rd: Redis,
    ctx: PaymentContext,
) -> None:
    """Test create Freekassa payment method"""
    result = await test_freekassa.create(ctx)
    if type(result) is str:
        assert result.startswith("Error")
    else:
        assert type(result.body) is bytes
        res = json.loads(result.body.decode("utf-8"))
        assert result.status_code == 200
        assert "url" in res.keys()
        assert res["url"].startswith("https://pay.fk.money/")


@pytest.mark.asyncio
async def test_confirm_freekassa(
    local_ip: str,
    test_freekassa: Freekassa,
    freekassa_confirm_data_mock: dict,
) -> None:
    """Test Freekassa webhook"""
    hash_string = ":".join(
        (
            settings.FREEK_SHOP_ID,
            str(freekassa_confirm_data_mock.AMOUNT),
            settings.FREEK_SECRET_2,
            str(freekassa_confirm_data_mock.MERCHANT_ORDER_ID),
        )
    )

    freekassa_confirm_data_mock.SIGN = hashlib.md5(
        hash_string.encode("utf8")
    ).hexdigest()

    confirm = await test_freekassa.confirmation(freekassa_confirm_data_mock)
    assert confirm == "YES" or confirm.startswith("ERROR: Already completed")


@pytest.mark.asyncio
async def test_confirm_verify_freekassa(
    local_ip: str,
    test_freekassa: Freekassa,
    freekassa_confirm_data_mock: dict,
    freekassa_confirm_trans_mock: TransactionFull,
    rd: Annotated[Redis, Depends(rdb)],
) -> None:
    """Test Freekassa verifying webhook data method"""
    verify_res = await verify(
        rd,
        freekassa_confirm_data_mock,
        freekassa_confirm_trans_mock,
    )
    assert verify_res == 1
