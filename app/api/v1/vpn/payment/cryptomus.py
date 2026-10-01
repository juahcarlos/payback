from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.responses import JSONResponse, Response

from app.core.exceptions import ClientError, InternalError, LocalizedAPIException
from app.core.logs import log
from app.domain.payments import PaymentData, PaymentSystem
from app.schemas import (
    CryptomusConfirmData,
    CryptomusCreateQueryParams,
)
from app.services.payments import CryptomusService, get_cryptomus_service


router = APIRouter(prefix="/vpn/payment")
router_lang = APIRouter(prefix="/{lang}/vpn/payment")


# TODO use POST and add schemas

@router.get("/create/cryptomus", response_class=JSONResponse)
@router_lang.get(
    "/create/cryptomus",
    response_class=JSONResponse,
    include_in_schema=False,
)
async def cryptomus_create(
        query_params: Annotated[CryptomusCreateQueryParams, Query()],
        request: Request,
        cryptomus_service: CryptomusService = Depends(get_cryptomus_service),  # noqa: B008
) -> JSONResponse:
    data = PaymentData(
        ip=request.client.host if request.client else "127.0.0.1",
        lang=query_params.lang,
        coupon=query_params.coupon,
        email=query_params.email,
        plan=query_params.plan,
        hidden_captcha=query_params.hidden_captcha,
        permanent=query_params.permanent,
        system=PaymentSystem.CRYPTOMUS,
    )

    try:
        result = await cryptomus_service.create_payment(data)
    except LocalizedAPIException as exc:
        raise exc
    except Exception as exc:
        log.error("cryptomus_create route: %s", exc)
        raise InternalError from exc

    return JSONResponse(result)


@router.post("/confirmation/cryptomus", response_class=Response)
async def cryptomus_confirmation(
        data: CryptomusConfirmData,
        request: Request,
        cryptomus_service: CryptomusService = Depends(get_cryptomus_service),  # noqa: B008
        sign: Annotated[str | None, Header()] = None,
) -> Response:
    raw_body = await request.body()

    try:
        await cryptomus_service.confirm_payment(raw_body=raw_body, header_sign=sign, data=data)
    except ClientError:
        return Response(status_code=400)
    except Exception as exc:  # noqa: BLE001
        log.error("cryptomus_create route: %s", exc)
        return Response(status_code=500)

    return Response(status_code=204)
