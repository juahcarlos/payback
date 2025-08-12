from typing import Annotated

from redis.asyncio.client import Redis
from db.database import DbQuery, db
from dbm.redis_db import rdb
from db.schemas import Mail, PaymentContext
from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from lib.domain.buy.trial import PaymentTrial

from libs.validators import check_lang

router = APIRouter(prefix="/payment")
router_lang = APIRouter(prefix="/{lang}/payment")


@router.post("/create/trial", response_class=Response)
@router_lang.get(
    "/trial",
    response_class=Response,
    summary="Create a free trial user account",
    description=(
        "Create new user account with free trial tariff, "
        "based on user's email, IP and language."
    ),
)
async def trial(
    db: Annotated[DbQuery, Depends(db)],
    rdb: Annotated[Redis, Depends(rdb)],
    data: Mail,
    request: Request,
    lang: Annotated[str, Depends(check_lang)] = "en",
) -> Response:
    """
    Create a free trial user via the base class Payment method create
    with currency="free" and plan=0.

    Args:
        db: Database handler.
        rdb: Redis handler.
        data: User email in Pydantic class EmailStr field.
        request: Fastapi HTTP request  to get client IP.
        lang: Language code, defaults to "en".

    Returns:
         Response: FastAPI Response with JSON content indicating success or failure.
    """
    email = data.email
    ctx = PaymentContext(
        email=email,
        ip=request.client.host,
        lang=lang,
        currency="free",
        plan=0,
    )
    trial = PaymentTrial(db, rdb)
    result = await trial.create(ctx)
    return Response(content=result, media_type="application/json")
