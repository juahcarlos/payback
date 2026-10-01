from dataclasses import asdict
from typing import Callable

import pytest
from httpx import AsyncClient

from app.domain.emails import RestoreCodeData
from app.schemas import RestoreCodeQueryParams
from app.services import get_code_service


BASE_BUY_ROUTE = "/vpn"


@pytest.fixture()
def mock_params_data() -> RestoreCodeQueryParams:
    return RestoreCodeQueryParams(email="someemail@test.com")


@pytest.fixture()
def mock_restore_data() -> RestoreCodeData:
    return RestoreCodeData(email="someemail@test.com")


@pytest.fixture()
def mock_get_code_service(mock_restore_data: RestoreCodeData) -> Callable:
    class MockCodeService:
        async def restore_access_code(self, email: str, ip: str) -> RestoreCodeData:
            return mock_restore_data

    def get_mock_code_service() -> MockCodeService:
        return MockCodeService()

    return get_mock_code_service


async def test_restore(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_code_service: Callable,
        mock_restore_data: RestoreCodeData,
        mock_params_data: RestoreCodeQueryParams,
) -> None:
    override_depends(get_code_service, mock_get_code_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/recovery",
        params=mock_params_data.model_dump(),
    )

    assert response.status_code == 200
    assert response.json() == asdict(mock_restore_data)
