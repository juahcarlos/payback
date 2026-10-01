from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.logs import log


router = APIRouter()


@router.get("/ping", response_class=JSONResponse, tags=["healthcheck"])
async def healthcheck(request: Request) -> JSONResponse:
    headers_as_string = ", ".join(
        f"{header_name}: {header_value}"
        for header_name, header_value in request.headers.items()
    )

    log.debug("healthcheck request headers: %s", headers_as_string)

    return JSONResponse(content={"ping": "pong!!"})

