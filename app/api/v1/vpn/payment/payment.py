from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core import exceptions as app_exceptions
from app.core.locale import get_current_locale
from app.schemas import (
    CouponCheckQueryParams,
    CouponCheckResponse,
    PaymentFailedResponse,
    PaymentSuccessResponse,
)
from app.services import (
    CouponService,
    TranslationService,
    get_coupon_service,
    get_translation_service,
)
from app.services.payments import PaymentService, get_payment_service


router = APIRouter(prefix="/vpn/payment")
router_lang = APIRouter(prefix="/{lang}/vpn/payment")


@router.get("/check_coupon", response_model=CouponCheckResponse)
@router_lang.get(
    "/check_coupon",
    response_model=CouponCheckResponse,
    include_in_schema=False,
)
async def check_coupon(
        query_params: Annotated[CouponCheckQueryParams, Query()],
        coupon_service: CouponService = Depends(get_coupon_service),  # noqa: B008
) -> CouponCheckResponse:
    result = await coupon_service.check_coupon(
        coupon_code=query_params.coupon,
        tariff=query_params.tariff,
    )
    if not result:
        raise app_exceptions.ErrorCouponInvalid()

    return CouponCheckResponse.model_validate(asdict(result))


@router.get("/fail", response_model=PaymentFailedResponse)
@router_lang.get(
    "/fail",
    response_model=PaymentFailedResponse,
    include_in_schema=False,
)
async def payment_fail(
        transalation_service: TranslationService = Depends(get_translation_service),  # noqa: B008
        locale: str = Depends(get_current_locale),
) -> PaymentFailedResponse:
    msg_1 = transalation_service.translate_message(
        key="vpn.payment.fail.header",
        locale=locale,
    )
    msg_2 = transalation_service.translate_message(
        key="vpn.payment.fail.message",
        locale=locale,
    )

    return PaymentFailedResponse(message=f"{msg_1}\n\n{msg_2}")


@router.get("/success", response_model=PaymentSuccessResponse)
@router_lang.get(
    "/success",
    response_model=PaymentSuccessResponse,
    include_in_schema=False,
)
async def payment_success(
        email_cookie: str | None = None,
        payment_service: PaymentService = Depends(get_payment_service),  # noqa: B008
) -> PaymentSuccessResponse:
    result = await payment_service.success(email_cookie)
    return PaymentSuccessResponse.model_validate(asdict(result))
