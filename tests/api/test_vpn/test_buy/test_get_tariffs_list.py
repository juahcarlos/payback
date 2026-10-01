from dataclasses import asdict
from typing import Callable

import pytest
from httpx import AsyncClient

from app.domain.tariffs import TariffReadModel
from app.services import get_tariff_service


BASE_BUY_ROUTE = "/vpn/buy"


@pytest.fixture()
def mock_tariffs_data() -> list[TariffReadModel]:
    return [
        TariffReadModel(
            id="1",
            date="date-1",
            month="1",
            count="20",
            economy="80%",
            popular=False,
            countText="1",
            countTextSum="11",
        ),
        TariffReadModel(
            id="2",
            date="date-2",
            month="1",
            count="20",
            economy="70%",
            popular=True,
            countText="1",
            countTextSum="11",
        ),
    ]


@pytest.fixture()
def mock_get_tariff_service(mock_tariffs_data: list[TariffReadModel]) -> Callable:
    class MockTariffService:
        async def get_tariffs(self) -> list[TariffReadModel]:
            return mock_tariffs_data

    def get_mock_tariff_service() -> MockTariffService:
        return MockTariffService()

    return get_mock_tariff_service


async def test_get_tariffs(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_tariff_service: Callable,
        mock_tariffs_data: list[TariffReadModel],
) -> None:
    override_depends(get_tariff_service, mock_get_tariff_service)

    response = await async_client.get(f"{BASE_BUY_ROUTE}/tariffs")

    assert response.status_code == 200
    assert response.json() == [asdict(td) for td in mock_tariffs_data]
