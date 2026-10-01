import secrets
import string
from dataclasses import replace
from datetime import UTC, datetime

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.exc import IntegrityError

from app.core import exceptions as app_exceptions
from app.core.config import settings
from app.core.locale import get_current_locale
from app.core.logs import log
from app.core.redis import get_redis
from app.domain.users import (
    UserCountModel,
    UserCreateModel,
    UserDataModel,
    UserPaymentInputData,
    UserReadModel,
    UserUpdateModel,
)
from app.repositories import UserDBRepo, get_user_repo
from app.services import CodeService, get_code_service
from app.utils.datetime import utc_now_naive


class UserService:
    def __init__(
            self,
            repo: UserDBRepo,
            code_service: CodeService,
            locale: str,
            redis: Redis,
    ) -> None:
        self.repo = repo
        self.code_service = code_service
        self.locale = locale
        self.redis = redis

        self.redis_users_count_key = (
            "active_users_count"
            if settings.prod
            else "active_users_count_stage"
        )
        self.redis_users_count_ttl = 60 * 5  # 5 minutes

    @staticmethod
    def generate_password() -> str:
        return "".join([
            secrets.choice(string.ascii_letters + string.digits)
            for _ in range(12)
        ]).lower()

    async def create_new_user(self, data: UserPaymentInputData) -> UserReadModel:
        access_code = await self.code_service.create_access_code()

        new_user_data = UserCreateModel(
            email=data.email,
            trial=data.trial,
            code=access_code,
            created=utc_now_naive(),
            version_page=2,
            expires=int(datetime.now(UTC).timestamp()) + 3600,
            password=self.generate_password(),
            reg_source=data.source,
            country_iso=data.country_iso,
            lang=self.locale,
        )

        for attempt in range(30):
            try:
                await self.repo.create_user(new_user_data)
                break
            except IntegrityError:
                if not await self.repo.get_user_by_code(new_user_data.code):
                    raise
                if attempt == 29:
                    log.error("UserService create_new_user: access code retries exhausted")
                    raise app_exceptions.InternalError() from None
                new_user_data = replace(
                    new_user_data,
                    code=await self.code_service.create_access_code(),
                )

        user = await self.repo.get_user_by_email(data.email)

        if not user:
            log.debug("UserService create_new_user: error creating user")
            raise app_exceptions.InternalError()

        return user

    async def get_or_create_user(
            self,
            data: UserPaymentInputData,
    ) -> UserReadModel:
        user = await self.repo.get_user_by_email(data.email)

        if not user:
            user = await self.create_new_user(data)
            log.debug("UserService get_or_create_user: new user created (%s)", data.email)

        return user

    # TODO: make repo's get user accept params to filter
    async def get_user_by_email(self, email: str) -> UserReadModel | None:
        return await self.repo.get_user_by_email(email=email)

    async def get_user_by_id(self, user_id: int) -> UserReadModel | None:
        return await self.repo.get_user_by_id(user_id=user_id)

    async def get_users_count(self) -> UserCountModel | None:
        redis_data = await self.redis.get(self.redis_users_count_key)
        if redis_data is not None:
            return UserCountModel(active=int(redis_data))

        log.debug("UserService get_users_count: no data in redis")

        db_data = await self.repo.get_active_users_count()
        if db_data:
            await self.redis.set(self.redis_users_count_key, db_data.active)
            await self.redis.expire(self.redis_users_count_key, self.redis_users_count_ttl)
            log.debug("UserService get_users_count: data added to redis")

        return db_data

    async def update_user_finished(self, data: UserUpdateModel) -> UserReadModel | None:
        await self.repo.update_user_full_finish(user_data=data)
        return await self.repo.get_user_by_email(email=data.email)

    async def update_user_subscription_deleted(self, user_data: UserDataModel) -> None:
        await self.repo.update_user_subscription_deleted(user_data=user_data)

    async def make_user_non_trial(self, user_id: int) -> None:
        await self.repo.update_user_trial(user_id=user_id, trial=False)


def get_user_service(
        repo: UserDBRepo = Depends(get_user_repo),  # noqa: B008
        code_service: CodeService = Depends(get_code_service),  # noqa: B008
        locale: str = Depends(get_current_locale),
        redis: Redis = Depends(get_redis),  # noqa: B008
) -> UserService:
    return UserService(
        repo=repo,
        code_service=code_service,
        locale=locale,
        redis=redis,
    )
