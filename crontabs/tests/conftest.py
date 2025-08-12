import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, List

import httpx
import pytest_asyncio

from config import settings
from crontabs.db.db_query import dbq as db
from dbm.schemas import TransactionFull, User, UserId

for n in [2, 3]:
    sys.path.append(str(Path(__file__).parents[n]))
    print(Path(__file__).parents[n])


def userr() -> User:
    """User data to insert before and delete after test"""
    return User(
        email=settings.TEST_EMAIL,
        created=datetime.now() - timedelta(hours=1),
        code=settings.TEST_CODE,
        trial=False,
        plan=settings.TEST_PLAN,
        lang=settings.TEST_LANG,
        expires=int((datetime.now() + timedelta(days=30)).strftime("%s")),
    )


def trans_cust_promo() -> TransactionFull:
    """
    Transation data to insert before and delete after
    test newcustomer promo mailing
    """
    return TransactionFull(
        system="freekassa",
        data="{}",
        days=30,
        amount=9.9,
        email=settings.TEST_EMAIL,
        created=datetime.now() - timedelta(days=23),
        expires=datetime.now() + timedelta(days=7) - timedelta(minutes=30),
        coupon=None,
        trial=False,
        version_page=2,
        country_iso="en",
        complete=1,
    )


def trans_cust_coupon() -> TransactionFull:
    """
    Transation data to insert before and delete after
    test newcustomer coupon mailing
    """
    return TransactionFull(
        system="freekassa",
        data="{}",
        days=30,
        amount=9.9,
        email=settings.TEST_EMAIL,
        created=datetime.now() - timedelta(days=1) - timedelta(minutes=30),
        expires=datetime.now() + timedelta(days=29),
        coupon=None,
        trial=True,
        version_page=2,
        country_iso="en",
        complete=1,
    )


@pytest_asyncio.fixture()
async def users_from_db() -> List[UserId]:
    """
    Wrap in List user data for testing payment reminder
    """
    return [
        UserId(
            email="srntsfrtnshjs@gmail.com",
            created="2024-03-01 18:58:40",
            cn="sec2417586",
            trial=None,
            version_page=None,
            code=None,
            coupon=None,
            expires=0,
            plan=30,
            country_iso=None,
            password=None,
            reg_source=None,
            dubious=0,
            ubscribed=0,
            lang="ru",
            partner_id=None,
            note=None,
            id=2417586,
        )
    ]


async def insert_user(user) -> None:
    """Delete (to avoid duplicate record error) and insert user to DB"""
    await db.delete_user(settings.TEST_EMAIL)
    await db.insert_email(user)
    get_new_user = await db.get_user_db(settings.TEST_EMAIL)
    await db.update_user_after_insert(get_new_user)


async def delete_user() -> None:
    """Delete user from DB"""
    await db.delete_user(settings.TEST_EMAIL)


@pytest_asyncio.fixture
async def ins_del_user() -> AsyncGenerator[UserId, None]:
    """Insert user before, yield and delete him after test"""
    user_ = userr()
    await insert_user(user_)

    user_ret = await db.get_user_by_email(settings.TEST_EMAIL)
    yield user_ret

    await delete_user()


@pytest_asyncio.fixture()
async def ins_del_user_no_yield() -> AsyncGenerator[httpx.AsyncClient, None]:
    """insert user, yield None, deletes user"""
    user_ = userr()
    await insert_user(user_)
    yield None
    await delete_user()


@pytest_asyncio.fixture
async def ins_del_user_nc_promo() -> AsyncGenerator[UserId, None]:
    """insert user, transaction, yield user, deletes user and transaction"""
    user_data = userr()
    await insert_user(user_data)
    trans_data = trans_cust_promo()
    trans = await db.insert_transaction(trans_data)

    user_ret = await db.get_user_by_email(settings.TEST_EMAIL)
    yield user_ret

    await delete_user()
    await db.delete_trans_by_id(trans.id)


@pytest_asyncio.fixture
async def ins_del_user_nc_coupon() -> AsyncGenerator[UserId, None]:
    """
    insert user, transaction, yield user,
    deletes user and transaction
    for news customer coupon tess
    """
    user_data = userr()
    await insert_user(user_data)
    trans_data = trans_cust_coupon()
    trans = await db.insert_transaction(trans_data)

    user_ret = await db.get_user_by_email(settings.TEST_EMAIL)
    yield user_ret

    await delete_user()
    await db.delete_trans_by_id(trans.id)
