import asyncio
from dbm.redis_db import redis_stright as rdb

from libs.logs import log


async def burning_mails() -> None:
    already = await rdb.get("blacklist:email:xoxy.uk")
    log.debug(f"already {already}")
    if already is None:
        with open("misc/burning-emails.txt", "r") as f:
            for row in f:
                key = "blacklist:email:" + row
                key = key.rstrip()
                await rdb.set(key, 1)

    log.debug("burning_mails done")


asyncio.run(burning_mails())
