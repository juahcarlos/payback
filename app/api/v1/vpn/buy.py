from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import JSONResponse, Response

from app.core import exceptions as app_exceptions
from app.core.logs import log
from app.schemas import (
    BuyResponse,
    FillingQueryParams,
    FillingResponse,
    TariffResponse,
)
from app.services import (
    BuyService,
    CookieService,
    TariffService,
    get_buy_service,
    get_cookie_service,
    get_tariff_service,
)


router = APIRouter(prefix="/vpn/buy")
router_lang = APIRouter(prefix="/{lang}/vpn/buy")


@router.get("", response_model=BuyResponse)
@router_lang.get("", response_model=BuyResponse, include_in_schema=False)
async def get_buy(
        request: Request,
        service: BuyService = Depends(get_buy_service),  # noqa: B008
) -> BuyResponse:
    ip = request.client.host if request.client else "127.0.0.1"
    data = await service.get_buy_data(ip)
    return BuyResponse.model_validate(asdict(data))


@router.get("/tariffs", response_model=list[TariffResponse])
async def get_tariffs_list(
        service: TariffService = Depends(get_tariff_service),  # noqa: B008
) -> list[TariffResponse]:
    tariffs = await service.get_tariffs()
    return [TariffResponse.model_validate(asdict(tariff)) for tariff in tariffs]


@router.get("/filling", response_model=FillingResponse)
@router_lang.get("/filling", response_model=FillingResponse, include_in_schema=False)
async def get_encrypted_email(
        query_params: Annotated[FillingQueryParams, Query()],
        buy_service: BuyService = Depends(get_buy_service),  # noqa: B008
        cookie_service: CookieService = Depends(get_cookie_service),  # noqa: B008
) -> FillingResponse:
    if not await buy_service.check_filling(query_params.id, query_params.token):
        log.warning(
            "get_encrypted_email route: buy_form_filling record doesn't exist "
            "(id = %s, token = %s)",
            query_params.id,
            query_params.token,
        )
        raise app_exceptions.Error404()

    encrypted_email = cookie_service.encrypt(query_params.email)

    return FillingResponse(encrypted_email=encrypted_email)


# TODO: is it used??
@router.get("/set_cookie", response_class=JSONResponse)
def set_cookie(
        response: Response,
        email: str,
        cookie_service: CookieService = Depends(get_cookie_service),  # noqa: B008
):
    value = cookie_service.encrypt(email)
    response.set_cookie(
        key="user",
        value=value,
        httponly=True,
        samesite='none',
        domain='whox.is',
    )
    return JSONResponse(content={"status": "OK"})
