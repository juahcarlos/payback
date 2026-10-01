import secrets
import string
import time
from collections.abc import Awaitable
from typing import cast

from fastapi import Depends
from redis.asyncio import Redis

from app.core import exceptions as app_exceptions
from app.core.config import settings
from app.core.logs import log
from app.core.redis import get_redis
from app.domain.emails import RestoreCodeData
from app.repositories import (
    UserDBRepo,
    get_user_repo,
)
from app.services.email import (
    EmailService,
    get_email_service,
)


class CodeService:
    RECOVERY_LIMIT_EMAIL_KEY = "recovery_email:{email}"
    RECOVERY_LIMIT_IP_KEY = "recovery_ip:{ip}"
    RECOVERY_LIMIT_SCRIPT = """
        if redis.call("EXISTS", KEYS[1]) == 1 or redis.call("EXISTS", KEYS[2]) == 1 then
            return 0
        end
        redis.call("SET", KEYS[1], 1, "EX", ARGV[1])
        redis.call("SET", KEYS[2], 1, "EX", ARGV[1])
        return 1
    """

    def __init__(
            self,
            user_repo: UserDBRepo,
            email_service: EmailService,
            redis: Redis,
    ) -> None:
        self.user_repo = user_repo
        self.email_service = email_service
        self.redis = redis

    @staticmethod
    def generate_access_code() -> str:
        random_part = "".join(
            [secrets.choice(string.ascii_letters + string.digits) for _ in range(10)]
        ).upper()
        return f"KEY{random_part}"

    # TODO: run email send as a task!
    async def restore_access_code(self, email: str, ip: str) -> RestoreCodeData:
        normalized_email = email.strip().lower()
        limit_acquired = await cast(
            Awaitable[int],
            self.redis.eval(
                self.RECOVERY_LIMIT_SCRIPT,
                2,
                self.RECOVERY_LIMIT_EMAIL_KEY.format(email=normalized_email),
                self.RECOVERY_LIMIT_IP_KEY.format(ip=ip),
                settings.email_recovery_interval_seconds,
            ),
        )
        if not limit_acquired:
            raise app_exceptions.ErrorRecoveryRateLimited()

        user_data = await self.user_repo.get_user_by_email(email)
        if (
            user_data is None
            or not user_data.code
            or (user_data.expires and user_data.expires < time.time())
        ):
            return RestoreCodeData(email=email)

        await self.email_service.send_restore_email(user_data)

        return RestoreCodeData(email=email, status="OK")

    async def create_access_code(self) -> str:
        max_attempts = 30
        current_attempt = 0
        while current_attempt < max_attempts:
            code = self.generate_access_code()
            if await self.user_repo.get_user_by_code(code):
                current_attempt += 1
                continue

            return code

        log.error(
            "CodeService create_access_code: max_attempts exceeded "
            "trying to generate unique access code"
        )
        raise app_exceptions.InternalError()


def get_code_service(
        email_service: EmailService = Depends(get_email_service),  # noqa: B008
        user_repo: UserDBRepo = Depends(get_user_repo),  # noqa: B008
        redis: Redis = Depends(get_redis),  # noqa: B008
) -> CodeService:
    return CodeService(user_repo=user_repo, email_service=email_service, redis=redis)
