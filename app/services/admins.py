import hashlib
import secrets

from fastapi import Depends
from passlib.context import CryptContext
from starlette.concurrency import run_in_threadpool

from app.domain.admins import AdminAuthReadData
from app.repositories import AdminAuthDBRepo, get_admin_auth_repo


password_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
    pbkdf2_sha256__rounds=600_000,
)


class AdminService:
    def __init__(
            self,
            auth_repo: AdminAuthDBRepo,
    ) -> None:
        self.auth_repo = auth_repo

    async def get_admin_by_username(self, username: str) -> AdminAuthReadData | None:
        return await self.auth_repo.get_admin_by_username(username=username)

    async def verify_password(
            self,
            admin: AdminAuthReadData,
            plain_password: str,
    ) -> bool:
        if password_context.identify(admin.password):
            return await run_in_threadpool(
                password_context.verify,
                plain_password,
                admin.password,
            )

        legacy_hash = hashlib.sha256(
            (
                plain_password
                + hashlib.sha256(plain_password.encode()).hexdigest()
            ).encode()
        ).hexdigest()
        if not secrets.compare_digest(admin.password, legacy_hash):
            return False

        upgraded_hash = await run_in_threadpool(password_context.hash, plain_password)
        await self.auth_repo.update_password_hash(
            username=admin.username,
            expected_hash=admin.password,
            password_hash=upgraded_hash,
        )
        return True


def get_admin_service(
        auth_repo: AdminAuthDBRepo = Depends(get_admin_auth_repo),  # noqa: B008
) -> AdminService:
    return AdminService(auth_repo=auth_repo)
