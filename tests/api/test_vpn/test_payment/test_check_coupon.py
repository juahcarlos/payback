from dataclasses import asdict
from typing import Callable

import pytest
from httpx import AsyncClient

from app.domain.coupons import CouponCheckModel
from app.services import get_coupon_service
from app.schemas import CouponCheckQueryParams


BASE_BUY_ROUTE = "/vpn/payment"


@pytest.fixture()
def mock_check_params() -> CouponCheckQueryParams:
    return CouponCheckQueryParams(coupon="COUPON123")


@pytest.fixture()
def mock_check_result() -> CouponCheckModel:
    return CouponCheckModel(percent=20, prolong=30)


@pytest.fixture()
def mock_check_no_result() -> None:
    return None


@pytest.fixture()
def mock_get_coupon_service(mock_check_result: CouponCheckModel) -> Callable:
    class MockCouponService:
        async def check_coupon(
                self,
                coupon_code: str,
                tariff: str | None = None,
        ) -> CouponCheckModel:
            return mock_check_result

    def get_mock_coupon_service() -> MockCouponService:
        return MockCouponService()

    return get_mock_coupon_service


@pytest.fixture()
def mock_get_no_coupon_service(mock_check_no_result: None) -> Callable:
    class MockCouponService:
        async def check_coupon(
                self,
                coupon_code: str,
                tariff: str | None = None,
        ) -> CouponCheckModel:
            return mock_check_no_result

    def get_mock_coupon_service() -> MockCouponService:
        return MockCouponService()

    return get_mock_coupon_service


async def test_check(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_coupon_service: Callable,
        mock_check_params: CouponCheckQueryParams,
        mock_check_result: CouponCheckModel,
) -> None:
    override_depends(get_coupon_service, mock_get_coupon_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/check_coupon",
        params=mock_check_params.model_dump(),
    )

    assert response.status_code == 200
    assert response.json() == asdict(mock_check_result)


async def test_check_none(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_no_coupon_service: Callable,
        mock_check_params: CouponCheckQueryParams,
) -> None:
    override_depends(get_coupon_service, mock_get_no_coupon_service)

    response = await async_client.get(
        f"{BASE_BUY_ROUTE}/check_coupon",
        params=mock_check_params.model_dump(),
    )

    assert response.status_code == 400
