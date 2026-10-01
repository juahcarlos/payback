from base64 import b64encode
from typing import Callable

import pytest
from httpx import AsyncClient

from app.core.redis import get_redis
from app.core.config import settings
from app.domain.admins import AdminAuthReadData
from app.services import get_server_service, get_admin_service


BASE_SERVERS_ROUTE = "/admin/servers"


@pytest.fixture()
def mock_admin_username():
    return "superadmin"


@pytest.fixture()
def mock_admin_password():
    return "superpass"


@pytest.fixture()
def mock_get_admin_service(mock_admin_username: str, mock_admin_password: str) -> Callable:
    class MockAdminService:
        async def get_admin_by_username(self, username) -> AdminAuthReadData | None:
            return (
                AdminAuthReadData(username=mock_admin_username, password=mock_admin_password)
                if username == mock_admin_username
                else None
            )

        async def verify_password(self, admin, plain_password) -> bool:
            return admin.password == plain_password

    def get_mock_admin_service() -> MockAdminService:
        return MockAdminService()

    return get_mock_admin_service


def basic_auth_header(username: str, password: str) -> dict:
    credentials = f"{username}:{password}"
    encoded = b64encode(credentials.encode("utf-8")).decode("utf-8")
    return {"Authorization": f"Basic {encoded}"}


@pytest.fixture()
def mock_get_redis() -> Callable:
    class MockRedis:
        def __init__(self) -> None:
            self.failed_attempts: dict[str, list[int]] = {}

        async def eval(
                self,
                _script: str,
                _numkeys: int,
                key: str,
                now: int,
                window: int,
                limit: int,
                member: str,
        ) -> int:
            attempts = self.failed_attempts.setdefault(key, [])
            attempts[:] = [timestamp for timestamp in attempts if timestamp > now - window]
            if len(attempts) >= limit:
                return 0
            attempts.append(now)
            return 1

    client = MockRedis()

    async def get_mock_redis() -> MockRedis:
        return client

    return get_mock_redis


async def test_admin_requires_login(async_client: AsyncClient):
    response = await async_client.get(BASE_SERVERS_ROUTE)
    assert response.status_code == 401

    response = await async_client.get(f"{BASE_SERVERS_ROUTE}/countries")
    assert response.status_code == 401


async def test_admin_login_ok(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_server_service,
        mock_get_admin_service,
        mock_get_redis,
        mock_admin_username,
        mock_admin_password,
):
    override_depends(get_server_service, mock_get_server_service)
    override_depends(get_admin_service, mock_get_admin_service)
    override_depends(get_redis, mock_get_redis)

    response = await async_client.get(
        f"{BASE_SERVERS_ROUTE}/countries",
        headers=basic_auth_header(mock_admin_username, mock_admin_password)
    )

    assert response.status_code == 200


async def test_admin_login_fail(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_admin_service,
        mock_get_redis,
        mock_admin_username,
):
    override_depends(get_admin_service, mock_get_admin_service)
    override_depends(get_redis, mock_get_redis)

    response = await async_client.get(
        f"{BASE_SERVERS_ROUTE}/countries",
        headers=basic_auth_header(mock_admin_username, "some_wrong_pass")
    )

    assert response.status_code == 401


async def test_admin_login_rate_limited(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_admin_service,
        mock_get_redis,
        mock_admin_username,
):
    override_depends(get_admin_service, mock_get_admin_service)
    override_depends(get_redis, mock_get_redis)

    for _ in range(settings.auth_max_failed_attempts + 1):
        response = await async_client.get(
            f"{BASE_SERVERS_ROUTE}/countries",
            headers=basic_auth_header(mock_admin_username, "some_wrong_pass")
        )

    assert response.status_code == 429
