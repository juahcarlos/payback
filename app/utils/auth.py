import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import AuthError
from app.core.redis import get_redis
from app.services import AdminService, get_admin_service
from app.utils.rate_limiter import rate_limit_failed_auth


security = HTTPBasic()


def get_current_username(
        credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> str:
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = settings.prometheus_login
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = settings.prometheus_password
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


async def verify_basic_auth(
        request: Request,
        credentials: HTTPBasicCredentials = Depends(security),  # noqa: B008
        service: AdminService = Depends(get_admin_service),  # noqa: B008
        redis: Redis = Depends(get_redis),  # noqa: B008
) -> None:
    admin_user = await service.get_admin_by_username(credentials.username)
    if not admin_user:
        await rate_limit_failed_auth(request, redis)
        raise AuthError()

    if not await service.verify_password(
        admin=admin_user,
        plain_password=credentials.password,
    ):
        await rate_limit_failed_auth(request, redis)
        raise AuthError()

    return None
