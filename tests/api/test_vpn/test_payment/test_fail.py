from typing import Callable

import pytest
from httpx import AsyncClient

from app.services import get_translation_service
from app.schemas import PaymentFailedResponse


BASE_BUY_ROUTE = "/vpn/payment"


@pytest.fixture()
def mock_response(mock_message: str) -> PaymentFailedResponse:
    return PaymentFailedResponse(message=f"{mock_message}\n\n{mock_message}")


async def test_fail(
        async_client: AsyncClient,
        mock_response: PaymentFailedResponse,
) -> None:
    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/fail",
    )

    assert response.json() == mock_response.model_dump()
