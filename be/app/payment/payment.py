import json
from typing import Annotated, Optional

from redis.asyncio.client import Redis
from db.database import DbQuery, db
from dbm.redis_db import rdb
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from lib.domain.buy.buy import check_coupon
from lib.domain.buy.payment import PaymentAll

router = APIRouter(prefix="/payment")
router_lang = APIRouter(prefix="/{lang}/payment")


@router.get("/check_coupon", response_class=Response)
@router_lang.get(
    "/check_coupon",
    response_class=Response,
    include_in_schema=False,
    summary="Check if the coupon exists",
    description=(
            "Check whether the coupon is present in the database,"
            "is not expired, and can be applied."
    ),
)
async def get_check_coupon(
    db: Annotated[DbQuery, Depends(db)],
    coupon: str = None,
    tariff: Optional[str] = None,
) -> Response:
    """
    Check if the coupon exists in the database, is valid
    and can be applied to the given tariff.

    Args:
        db: Database handler.
        coupon: Coupon ID.
        tariff: Tariff name to apply the coupon to. Defaults to None

    Returns:
         Response: FastAPI Response with JSON the coupon validation result.
    """
    result = await check_coupon(db, coupon, tariff)
    return Response(content=json.dumps(result), media_type="application/json")


@router.get("/fail", response_class=Response)
@router_lang.get(
    "/fail",
    response_class=Response,
    include_in_schema=False,
    summary="Handle payment failure callback",
    description=(
            "Endpoint to handle redirects from the payment system when a payment "
            "fails or encounters an issue."
    ),
)
async def payment_fail(
    db: Annotated[DbQuery, Depends(db)],
    email_cookie: Optional[str | None] = None,
) -> Response:
    """
    Handle payment failure redirects from the payment system.
    Process data using the database only if email cookie is present.

    Args:
        db: Database handler.
        email_cookie: Optional email identifier from user cookie.

    Returns:
        Response: JSON response with the result of the failure handling.
    """
    result = await PaymentAll(db, rdb).fail(email_cookie)
    return Response(
        content=json.dumps(result, ensure_ascii=False), media_type="application/json"
    )


@router.get("/success", response_class=Response)
@router_lang.get(
    "/success",
    response_class=Response,
    include_in_schema=False,
    summary="Handle payment success callback",
    description=(
            "Receives redirects from the payment system"
            "if a payment has been completed successfully. "
    ),
)
async def payment_success(
    db: Annotated[DbQuery, Depends(db)],
    request: Request,
    email_cookie: Optional[str] = None,
) -> Response:
    """
    Client is redirected to this endpoint by the payment system upon successful payment.
    Processes data using the database and client IP from the request.

    Args:
        db: Database handler.
        request: FastAPI request object to access client IP.
        email_cookie: Optional email identifier from user cookie.

    Returns:
        Response: JSON response with the result of the success handling.
    """
    result = await PaymentAll(db, rdb, request.client.host).success(email_cookie)
    return Response(
        content=json.dumps(result, ensure_ascii=False), media_type="application/json"
    )
