import hashlib
import secrets
import time
from collections.abc import Awaitable
from typing import cast

from fastapi import Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import AuthRateLimitedError


FAILED_AUTH_SCRIPT = """
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local window = tonumber(ARGV[2])
    local limit = tonumber(ARGV[3])

    redis.call("ZREMRANGEBYSCORE", key, "-inf", now - window)
    if redis.call("ZCARD", key) >= limit then
        return 0
    end

    redis.call("ZADD", key, now, ARGV[4])
    redis.call("PEXPIRE", key, window)
    return 1
"""


async def rate_limit_failed_auth(request: Request, redis: Redis) -> None:
    ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(ip.encode("utf-8")).hexdigest()
    allowed = await cast(
        Awaitable[int],
        redis.eval(
            FAILED_AUTH_SCRIPT,
            1,
            f"admin_failed_auth:{ip_hash}",
            int(time.time() * 1000),
            settings.auth_window_seconds * 1000,
            settings.auth_max_failed_attempts,
            secrets.token_hex(16),
        ),
    )
    if not allowed:
        raise AuthRateLimitedError()
