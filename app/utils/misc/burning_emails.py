from pathlib import Path

from redis.asyncio import Redis

from app.core.logs import log


BASE_DIR = Path(__file__).resolve().parent
FILE_PATH = BASE_DIR / "burning-emails.txt"


async def load_burning_emails(redis: Redis) -> None:
    already_loaded = await redis.get("blacklist:email:xoxy.uk")
    if already_loaded:
        log.debug("Burning emails have been already loaded")
        return

    with open(FILE_PATH, encoding="utf-8") as f:
        for line in f:
            key = f"blacklist:email:{line.strip()}"
            await redis.set(key, 1)

    log.debug("Burning emails have been successfully loaded")
