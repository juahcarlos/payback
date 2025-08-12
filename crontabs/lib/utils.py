import hashlib
import json
from typing import Optional

from config import settings
from crontabs.db.db_query import dbq
from crontabs.db.schemas import UserReminder


def languages():
    """Provide translated to given languages texts"""
    with open("langs/subjects.json", "r") as subj:
        return json.loads(subj.read())


langs = languages()


async def get_emails(mail_from_args: Optional[str | None] = None):
    """
    Query email addresses of users whose purchased tariff
    expired between two days ago and one day from now,
    to remind them of payment and offer a discount.
    """
    if mail_from_args:
        users = [await dbq.get_user_db(mail_from_args)]
    else:
        users = await dbq.get_all_users_reminder()
    return users


def get_unsubscribe_token(email: str) -> str:
    """Generate the token to unsubscribe from mailings"""
    token = hashlib.sha1(
        (email + ":" + settings.UNSUBSCRIBE_SECRET).encode("utf-8")
    ).hexdigest()
    return token


async def get_users(users: list, no_unsubscribe=None) -> list:
    """Set unsubscribe token to the given users list"""
    result = []

    for user in users:
        user_pd = UserReminder(**user.__dict__)

        if not no_unsubscribe:
            user_pd.unsubscribe_token = get_unsubscribe_token(user_pd.email)
        result.append(user_pd)

    return result
