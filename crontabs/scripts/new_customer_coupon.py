import asyncio
from typing import List

from crontabs.db.db_query import dbq as db
from crontabs.lib.mail import send_all_new_customer_coupon


async def coupon() -> List[str | None]:
    """
    Fetches a list of users who purchased yesterday
    to send them discount coupons.
    """
    users = await db.get_customer_coupon_db()
    res = await send_all_new_customer_coupon(users)
    return res


asyncio.run(coupon())
