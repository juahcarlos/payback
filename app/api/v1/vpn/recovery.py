from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request

from app.schemas import RestoreCodeQueryParams, RestoreCodeResponse
from app.services import CodeService, get_code_service


router = APIRouter(prefix="/vpn")
router_lang = APIRouter(prefix="/{lang}/vpn")


@router.get("/recovery", response_model=RestoreCodeResponse)
@router_lang.get("/recovery", response_model=RestoreCodeResponse, include_in_schema=False)
async def resotore_code(
        request: Request,
        query_params: Annotated[RestoreCodeQueryParams, Query()],
        service: CodeService = Depends(get_code_service),  # noqa: B008
) -> RestoreCodeResponse:
    ip = request.client.host if request.client else "unknown"
    result = await service.restore_access_code(query_params.email, ip)
    return RestoreCodeResponse.model_validate(asdict(result))
