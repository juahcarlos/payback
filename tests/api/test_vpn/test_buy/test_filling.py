from typing import Callable

import pytest
from httpx import AsyncClient

from app.schemas import FillingQueryParams
from app.services import get_buy_service, get_cookie_service


BASE_BUY_ROUTE = "/vpn/buy"


@pytest.fixture()
def mock_get_buy_service() -> Callable:
    class MockBuyService:
        async def check_filling(self, filling_id: int, token_str: str) -> bool:
            if filling_id == 1:
                return True

            return False

    def get_mock_buy_service() -> MockBuyService:
        return MockBuyService()

    return get_mock_buy_service


@pytest.fixture()
def mock_get_cookie_service() -> Callable:
    class MockCookieService:
        def encrypt(self, email: str) -> str:
            return email

    def get_mock_cookie_service() -> MockCookieService:
        return MockCookieService()

    return get_mock_cookie_service


async def test_get_filling_true(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_buy_service: Callable,
        mock_get_cookie_service: Callable,
) -> None:
    email = "someemail@test.com"
    override_depends(get_buy_service, mock_get_buy_service)
    override_depends(get_cookie_service, mock_get_cookie_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/filling",
        params=FillingQueryParams(id=1, token="token", email=email, lang="ru").model_dump(),
    )

    assert response.status_code == 200
    assert response.json() == {"encrypted_email": email}


async def test_get_filling_false(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_buy_service: Callable,
        mock_get_cookie_service: Callable,
) -> None:
    email = "someemail@test.com"
    override_depends(get_buy_service, mock_get_buy_service)
    override_depends(get_cookie_service, mock_get_cookie_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/filling",
        params=FillingQueryParams(id=2, token="token", email=email, lang="ru").model_dump(),
    )

    assert response.status_code == 404
