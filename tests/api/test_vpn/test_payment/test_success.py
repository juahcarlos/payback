from dataclasses import asdict
from typing import Callable

import pytest
from httpx import AsyncClient

from app.domain.payments import PaymentSuccess
from app.services.payments import get_payment_service


BASE_BUY_ROUTE = "/vpn/payment"


@pytest.fixture()
def mock_result() -> PaymentSuccess:
    return PaymentSuccess(message="OK")


@pytest.fixture()
def mock_get_payment_service(mock_result: PaymentSuccess) -> Callable:
    class MockPaymentService:
        async def success(self, email_cookie: str) -> PaymentSuccess:
            return mock_result

    def get_mock_payment_service() -> MockPaymentService:
        return MockPaymentService()

    return get_mock_payment_service


async def test_success(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_result: PaymentSuccess,
        mock_get_payment_service: Callable,
) -> None:
    override_depends(get_payment_service, mock_get_payment_service)
    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/success",
    )

    assert response.json() == asdict(mock_result)
