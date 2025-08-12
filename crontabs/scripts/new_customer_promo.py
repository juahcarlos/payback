import asyncio
from typing import List

from crontabs.db.db_query import dbq as db
from crontabs.lib.mail import send_all_new_customer_promo


async def promo() -> List[str | None]:
    """
    Collect customers who bought a 30-day tariff
    and whose subscription ends within 7 days,
    to offer a 35% discount on a 1-year tariff.
    """
    users = await db.get_customer_promo_db()
    res = await send_all_new_customer_promo(users)
    return res


asyncio.run(promo())
