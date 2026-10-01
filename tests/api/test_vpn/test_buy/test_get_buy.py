from dataclasses import asdict
from typing import Callable

import pytest
from httpx import AsyncClient

from app.domain.buy_form_filling import BuyData
from app.services import get_buy_service


BASE_BUY_ROUTE = "/vpn/buy"


@pytest.fixture()
def mock_buy_data() -> BuyData:
    return BuyData(
        filling_id=12345,
        filling_token="filling_token",
        hidden_captcha="captcha",
    )


@pytest.fixture()
def mock_get_buy_service(mock_buy_data: BuyData) -> Callable:
    class MockBuyService:
        async def get_buy_data(self, ip: str = "127.0.0.1") -> BuyData:
            return mock_buy_data

    def get_mock_buy_service() -> MockBuyService:
        return MockBuyService()

    return get_mock_buy_service


async def test_buy(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_buy_service: Callable,
        mock_buy_data: BuyData,
) -> None:
    override_depends(get_buy_service, mock_get_buy_service)

    response = await async_client.get(BASE_BUY_ROUTE)

    assert response.status_code == 200
    assert response.json() == asdict(mock_buy_data)
