from dataclasses import asdict
from time import time

from sqlalchemy import delete, func, insert, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.users import (
    UserCountModel,
    UserCreateModel,
    UserDataModel,
    UserReadModel,
    UserUpdateModel,
)
from app.models import Users
from app.utils.email import normalize_email

from .base import BaseDBRepo


class UserDBRepo(BaseDBRepo):

    # CREATE

    async def create_user(self, user_data: UserCreateModel) -> UserReadModel | None:
        values = asdict(user_data)
        values["email"] = normalize_email(user_data.email)
        try:
            async with self.create_session() as session:
                async with session.begin():
                    user = Users(dubious=False, subscribed=False, **values)
                    session.add(user)
                    await session.flush()
                    setattr(user, "cn", f"sec{user.id}")  # noqa: B010
        except IntegrityError:
            existing_user = await self.get_user_by_email(values["email"])
            if existing_user is None:
                raise
            return existing_user

        return UserReadModel(
            **{
                column.key: getattr(user, column.key)
                for column in Users.__table__.columns
            }
        )

    async def insert_new_user(self, user_data: UserCreateModel) -> None:
        values = asdict(user_data)
        values["email"] = normalize_email(user_data.email)
        statement = insert(Users).values(
            dubious=0,
            subscribed=0,
            **values,
        )
        await self.insert_only(statement)

    # READ

    async def get_user_by_cn(self, cn: str) -> UserReadModel | None:
        statement = select(Users).where(Users.cn == cn)
        result = await self.select_one(statement, UserReadModel)
        return result

    async def get_user_by_email(self, email: str) -> UserReadModel | None:
        email = normalize_email(email)
        statement = select(Users).where(Users.email == email)
        result = await self.select_one(statement, UserReadModel)
        return result

    async def get_user_by_email_for_update(
            self,
            session: AsyncSession,
            email: str,
    ) -> Users | None:
        statement = (
            select(Users)
            .where(Users.email == normalize_email(email))
            .with_for_update()
        )
        result = await session.execute(statement)
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> UserReadModel | None:
        statement = select(Users).where(Users.id == user_id)
        result = await self.select_one(statement, UserReadModel)
        return result

    async def get_user_by_code(self, code: str) -> UserReadModel | None:
        statement = select(Users).where(Users.code == code)
        result = await self.select_one(statement, UserReadModel)
        return result

    async def get_active_users_count(self) -> UserCountModel | None:
        statement = (
            select(func.count(Users.id).label("active"))
            .where(
                Users.trial == 0,
                Users.expires > int(time()),
                or_(Users.cn.isnot(None), Users.cn != ""),
            )
        )
        return await self.select_one(statement, UserCountModel)

    # UPDATE

    async def update_user_subscription_deleted(self, user_data: UserDataModel) -> None:
        statement = (
            update(Users)
            .where(Users.id == user_data.user_id)
            .values(
                expires=user_data.expires,
                plan=user_data.plan,
                subscribed=user_data.subscribed,
            )
        )
        await self.update_only(statement)

    async def update_cn(self, email: str, cn: str) -> None:
        statement = update(Users).where(Users.email == normalize_email(email)).values(cn=cn)
        await self.update_only(statement)

    async def update_user_expires(self, email: str, expires: int) -> None:
        statement = (
            update(Users)
            .where(Users.email == normalize_email(email))
            .values(expires=expires)
        )
        await self.update_only(statement)

    async def update_user_coupon(self, email: str, coupon: str) -> None:
        statement = (
            update(Users)
            .where(Users.email == normalize_email(email))
            .values(coupon=coupon)
        )
        await self.update_only(statement)

    async def update_user_full_finish(self, user_data: UserUpdateModel) -> None:
        statement = (
            update(Users)
            .where(
                Users.email == normalize_email(user_data.email)
            )
            .values(
                plan=user_data.plan,
                code=user_data.code,
                coupon=user_data.coupon,
                expires=user_data.expires,
                trial=user_data.trial,
            )
        )
        await self.update_only(statement)

    async def update_user_trial(self, user_id: int, trial: bool) -> None:
        statement = (
            update(Users)
            .where(
                Users.id == user_id
            )
            .values(
                trial=trial,
            )
        )
        await self.update_only(statement)

    # DELETE

    async def delete_user_by_email(self, email: str) -> None:
        statement = delete(Users).where(Users.email == normalize_email(email))
        await self.delete(statement)

    async def delete_user_by_id(self, user_id: int) -> None:
        statement = delete(Users).where(Users.id == user_id)
        await self.delete(statement)


def get_user_repo() -> UserDBRepo:
    return UserDBRepo()
