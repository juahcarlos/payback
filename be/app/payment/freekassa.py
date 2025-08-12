import json
from typing import Annotated, Optional

from redis.asyncio.client import Redis
from db.database import DbQuery, db
from dbm.redis_db import rdb
from db.schemas import FreekassaConfirmData
from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse, Response
from lib.domain.buy.freekassa import Freekassa, PaymentContext

from config import settings
from libs.validators import check_lang

router = APIRouter(prefix="/payment")
router_lang = APIRouter(prefix="/{lang}/payment")


@router.get("/create/freekassa", response_class=Response)
@router_lang.get(
    "/create/freekassa",
    response_class=Response,
    include_in_schema=False,
)
async def freekassa_create(
    db: Annotated[DbQuery, Depends(db)],
    rdb: Annotated[Redis, Depends(rdb)],
    request: Request,
    lang: Annotated[str, Depends(check_lang)] = "en",
    coupon: Optional[str] = None,
    email: Optional[str] = None,
    plan: Optional[str] = None,
    currency: Optional[str] = "freekassa",
) -> Response:
    context = PaymentContext(
        email=email,
        coupon=coupon,
        plan=plan,
        lang=lang,
        ip=request.client.host,
        currency=currency,
    )

    freekassa = Freekassa(db, rdb)
    result = await freekassa.create(context)

    if result == "fail":
        return RedirectResponse(settings.BASE_URL + "/fail")
    return Response(content=json.dumps(result), media_type="application/json")


@router.get(
    "/confirmation/freekassa",
    response_class=Response,
    summary="Handle Freekassa payment webhook",
    description=(
            "Receives webhook call from the Freekassa payment system"
            "to confirm that payment was successfull and update the "
            "transaction record in the database by setting compete=1. "
    ),
)
async def freekassa_confirmation(
    db: Annotated[DbQuery, Depends(db)],
    rdb: Annotated[Redis, Depends(rdb)],
    request: Request,
    intid: Optional[str | int] = None,
    MERCHANT_ORDER_ID: Optional[str | int] = None,
    SIGN: Optional[str] = None,
    MERCHANT_ID: Optional[str] = None,
    AMOUNT: Optional[str | float | int] = None,
    P_EMAIL: Optional[str] = None,
    P_PHONE: Optional[str | int] = None,
    CUR_ID: Optional[str | int] = None,
    payer_account: Optional[str | int] = None,
    commission: Optional[str | float | int] = None,
) -> str | None:
    """
    Client is redirected to this endpoint by the
    payment system upon successful payment.
    Processes data using the database and client IP from the request.

    Args:
        data: Freekassa webhook data (FreekassaConfirmData).

    Returns:
        str: "YES" if confirmation succeeded,otherwise the error message
    """
    data = FreekassaConfirmData(
        intid=intid,
        MERCHANT_ORDER_ID=MERCHANT_ORDER_ID,
        SIGN=SIGN,
        MERCHANT_ID=MERCHANT_ID,
        AMOUNT=AMOUNT,
        P_EMAIL=P_EMAIL,
        P_PHONE=P_PHONE,
        CUR_ID=CUR_ID,
        payer_account=payer_account,
        commission=commission,
        ip=request.client.host,
    )

    result = await Freekassa(db, rdb).confirmation(data)
    if result == "fail":
        return RedirectResponse(settings.BASE_URL + "/fail")

    return result
