from typing import List

import pytest

from config import settings
from crontabs.db.schemas import UserReminder
from crontabs.lib.mail import (
    RemindRender,
    send_all_reminder,
)
from crontabs.lib.utils import get_emails, get_unsubscribe_token, get_users
from dbm.schemas import UserId


@pytest.mark.asyncio
async def test_tmpl(users_from_db: List[UserId]) -> None:
    """Test template renderer"""
    body = await RemindRender().render(users_from_db[0])
    assert "2008-" in body


@pytest.mark.asyncio
async def test_token() -> None:
    """Test unsubscribe token generator"""
    token = get_unsubscribe_token(settings.TEST_EMAIL)
    assert token == settings.TEST_TOKEN


@pytest.mark.asyncio
async def test_get_emails(ins_del_user_no_yield: None) -> None:
    """Test query email addresses for reminder mailing"""
    result = await get_emails(settings.TEST_EMAIL)
    assert type(result) is list
    assert len(result) > 0
    assert type(result[0]) is UserId
    assert result[0].email == settings.TEST_EMAIL


@pytest.mark.asyncio
async def test_get_users(users_from_db: List[UserId]) -> None:
    """Test function sets unsubscript token to users in reminder mailing list"""
    result = await get_users(users_from_db)
    assert type(result) is list
    assert len(result) > 0
    assert type(result[0]) is UserReminder
    assert result[0].email == settings.TEST_EMAIL
    assert result[0].unsubscribe_token is not None


@pytest.mark.asyncio
async def test_send_all(
    ins_del_user_no_yield: None, users_from_db: List[UserId]
) -> None:
    """Test send mails to users from payment reminder list"""
    res = await send_all_reminder(users_from_db)
    print("res", res)
    if res is not None:
        for r in res:
            if r is not None:
                assert r[0] == "" or r[0] is None
                assert r[1] == 200
