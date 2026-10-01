import hashlib
from dataclasses import dataclass

import pytest

from app.domain.admins import AdminAuthReadData
from app.services.admins import AdminService, password_context


@dataclass
class FakeAdminAuthRepo:
    updated_hash: str | None = None

    async def update_password_hash(
            self,
            username: str,
            expected_hash: str,
            password_hash: str,
    ) -> None:
        assert username == "admin"
        assert expected_hash
        self.updated_hash = password_hash


def legacy_password_hash(password: str) -> str:
    salt = hashlib.sha256(password.encode()).hexdigest()
    return hashlib.sha256((password + salt).encode()).hexdigest()


@pytest.mark.anyio
async def test_legacy_admin_password_is_upgraded_after_successful_login() -> None:
    repo = FakeAdminAuthRepo()
    service = AdminService(auth_repo=repo)
    old_hash = legacy_password_hash("correct horse battery staple")
    admin = AdminAuthReadData(username="admin", password=old_hash)

    assert await service.verify_password(admin, "correct horse battery staple")
    assert repo.updated_hash is not None
    assert repo.updated_hash != old_hash
    assert password_context.identify(repo.updated_hash) == "pbkdf2_sha256"
    assert password_context.verify("correct horse battery staple", repo.updated_hash)

    upgraded_admin = AdminAuthReadData(username="admin", password=repo.updated_hash)
    assert await service.verify_password(upgraded_admin, "correct horse battery staple")
    assert not await service.verify_password(upgraded_admin, "wrong password")


@pytest.mark.anyio
async def test_wrong_legacy_admin_password_does_not_change_hash() -> None:
    repo = FakeAdminAuthRepo()
    service = AdminService(auth_repo=repo)
    admin = AdminAuthReadData(
        username="admin",
        password=legacy_password_hash("correct horse battery staple"),
    )

    assert not await service.verify_password(admin, "wrong password")
    assert repo.updated_hash is None
