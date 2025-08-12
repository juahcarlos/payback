from typing import List

import pytest

from config import settings
from crontabs.db.db_query import dbq as db
from crontabs.db.schemas import CustomerPromo
from crontabs.lib.mail import (
    render_body_new_customer_coupon,
    send_all_new_customer_coupon,
)
from dbm.schemas import UserId


@pytest.mark.asyncio
async def test_tmpl() -> None:
    for lang in ["en", "es", "fr", "it", "jp", "nl", "pl", "pt", "ru", "tr", "zh"]:
        body = await render_body_new_customer_coupon(lang, settings.TEST_EMAIL)
        assert (
            f"https://whoer.net/{lang}/unsubscribe" in body
            or "https://whoer.net/unsubscribe" in body
        )
        assert "<!DOCTYPE html PUBLIC" in body
        print("is in", "<!DOCTYPE html PUBLIC" in body, lang)


@pytest.mark.asyncio
async def test_get_user(ins_del_user_nc_coupon: None) -> None:
    """Test query mails for new customer promo list"""
    result = await db.get_customer_coupon_db()
    assert type(result) is list
    assert len(result) > 0
    assert type(result[0]) is CustomerPromo
    assert result[0].address == settings.TEST_EMAIL


@pytest.mark.asyncio
async def test_send_all(
    ins_del_user_no_yield: None, users_from_db: List[UserId]
) -> None:
    """Test send mails to users from new customer coupon list"""
    res = await send_all_new_customer_coupon(users_from_db)

    for r in res:
        if r is not None:
            assert r[0] == "" or r[0] is None
            assert r[1] == 200
