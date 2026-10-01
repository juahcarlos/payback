from sqlalchemy import select, update

from app.domain.admins import AdminAuthReadData
from app.models import AdminAuth

from .base import BaseDBRepo


class AdminAuthDBRepo(BaseDBRepo):

    # READ

    async def get_admin_by_username(self, username: str) -> AdminAuthReadData | None:
        statement = select(
            AdminAuth.username,
            AdminAuth.password,
        ).where(AdminAuth.username == username)
        return await self.select_one(statement, AdminAuthReadData)

    async def update_password_hash(
            self,
            username: str,
            expected_hash: str,
            password_hash: str,
    ) -> None:
        statement = (
            update(AdminAuth)
            .where(
                AdminAuth.username == username,
                AdminAuth.password == expected_hash,
            )
            .values(password=password_hash)
        )
        await self.update_only(statement)


def get_admin_auth_repo() -> AdminAuthDBRepo:
    return AdminAuthDBRepo()
