from typing import Callable, Any

import pytest
from httpx import AsyncClient

from app.domain.payments import PaymentData
from app.services.payments import get_cryptomus_service
from app.schemas import CryptomusCreateQueryParams, CryptomusConfirmData


BASE_BUY_ROUTE = "/vpn/payment"


@pytest.fixture()
def mock_payment_params() -> CryptomusCreateQueryParams:
    return CryptomusCreateQueryParams(
        email="email@test.com",
        coupon="coup",
        plan="360",
        hidden_captcha="hidden_for_sure",
        permanent=False,
        lang="ru",
    )


@pytest.fixture()
def mock_crypt_data() -> dict[str, str]:
    return {
        "some": "data",
        "other": "data",
    }


@pytest.fixture()
def mock_confirm_data() -> CryptomusConfirmData:
    return CryptomusConfirmData()


@pytest.fixture()
def mock_get_crypt_service(mock_crypt_data: dict[str, str]) -> Callable:
    class MockCryptomusService:
        async def create_payment(self, data: PaymentData) -> dict[str, Any]:
            return mock_crypt_data

        async def confirm_payment(self, raw_body: bytes, header_sign: str, data: CryptomusConfirmData) -> None:
            return

    def get_mock_crypt_service() -> MockCryptomusService:
        return MockCryptomusService()

    return get_mock_crypt_service


@pytest.fixture()
def mock_get_crypt_fail_service() -> Callable:
    class MockCryptomusService:
        async def create_payment(self, data: PaymentData) -> dict[str, Any]:
            raise Exception

        async def confirm_payment(self, raw_body: bytes, header_sign: str, data: CryptomusConfirmData) -> None:
            raise Exception

    def get_mock_crypt_service() -> MockCryptomusService:
        return MockCryptomusService()

    return get_mock_crypt_service


async def test_create(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_crypt_service: Callable,
        mock_crypt_data: dict[str, str],
        mock_payment_params: CryptomusCreateQueryParams,
) -> None:
    override_depends(get_cryptomus_service, mock_get_crypt_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/create/cryptomus",
        params=mock_payment_params.model_dump(),
    )

    assert response.status_code == 200
    assert response.json() == mock_crypt_data


async def test_create_fail(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_crypt_fail_service: Callable,
        mock_payment_params: CryptomusCreateQueryParams,
) -> None:
    override_depends(get_cryptomus_service, mock_get_crypt_fail_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/create/cryptomus",
        params=mock_payment_params.model_dump(),
    )

    assert response.status_code == 500


async def test_confirm(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_crypt_service: Callable,
        mock_confirm_data: CryptomusConfirmData,
) -> None:
    override_depends(get_cryptomus_service, mock_get_crypt_service)

    response = await async_client.post(
        f"{BASE_BUY_ROUTE}/confirmation/cryptomus",
        json=mock_confirm_data.model_dump(),
    )

    assert response.status_code == 204


async def test_confirm_fail(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_crypt_fail_service: Callable,
        mock_confirm_data: CryptomusConfirmData,
) -> None:
    override_depends(get_cryptomus_service, mock_get_crypt_fail_service)

    response = await async_client.post(
        f"{BASE_BUY_ROUTE}/confirmation/cryptomus",
        json=mock_confirm_data.model_dump(),
    )

    assert response.status_code == 500
