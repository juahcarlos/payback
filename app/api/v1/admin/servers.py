from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Query,
    Response,
    status,
)

from app.core import exceptions as app_exceptions
from app.schemas import (
    AdminServerCountriesResponse,
    AdminServerCreateRequest,
    AdminServerFormResponse,
    AdminServerPatchRequest,
    AdminServersQueryParams,
    AdminServersResponse,
    AdminServerStatsResponse,
    AdminServerUpdateRequest,
)
from app.services import (
    ServerService,
    UserService,
    get_server_service,
    get_user_service,
)
from app.utils.auth import verify_basic_auth


router = APIRouter(prefix="/admin/servers")


@router.get(
    "",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_model=AdminServersResponse,
)
async def admin_servers(
        query_params: Annotated[AdminServersQueryParams, Query()],
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
) -> AdminServersResponse:
    servers_data = await servers_service.get_full_servers_data(filters=query_params)
    return AdminServersResponse.from_domain(servers=servers_data)


@router.get(
    "/countries",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_model=AdminServerCountriesResponse,
)
async def admin_server_countries(
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
) -> AdminServerCountriesResponse:
    data = await servers_service.get_server_countries()
    return AdminServerCountriesResponse(data=data)


@router.get(
    "/stats",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_model=AdminServerStatsResponse,
)
async def admin_server_stats(
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
        users_service: UserService = Depends(get_user_service),  # noqa: B008
) -> AdminServerStatsResponse:
    users_data = await users_service.get_users_count()
    server_stats = await servers_service.get_servers_stat()

    stats = AdminServerStatsResponse()

    if server_stats:
        stats.total_servers = server_stats.total
        stats.online_servers = server_stats.online
        stats.offline_servers = server_stats.offline
        stats.average_load = server_stats.average_load
        stats.overdue_payments = server_stats.overdue_payments
        stats.overloaded_servers = server_stats.overloaded
        stats.server_errors = server_stats.errors

    if users_data:
        stats.active_users = users_data.active

    return stats


@router.get(
    "/{server_id}",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_model=AdminServerFormResponse,
)
async def admin_get_server(
        server_id: int,
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
) -> AdminServerFormResponse:
    server_data = await servers_service.get_server_form_data_by_id(server_id=server_id)
    if not server_data:
        raise app_exceptions.Error404()

    return AdminServerFormResponse.from_domain(data=server_data)


@router.patch(
    "/{server_id}",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_class=Response,
)
async def admin_patch_server(
        server_id: int,
        data: AdminServerPatchRequest,
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
) -> Response:
    await servers_service.partially_update_server(server_id=server_id, data=data)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_model=AdminServerFormResponse,
)
async def admin_create_server(
        data: AdminServerCreateRequest,
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
) -> AdminServerFormResponse:
    server_data = await servers_service.create_server(server_data=data)
    if not server_data:
        raise app_exceptions.Error404()

    return AdminServerFormResponse.from_domain(data=server_data)


@router.put(
    "/{server_id}",
    dependencies=[Depends(verify_basic_auth)],
    include_in_schema=False,
    response_model=AdminServerFormResponse,
)
async def admin_update_server(
        server_id: int,
        data: AdminServerUpdateRequest,
        servers_service: ServerService = Depends(get_server_service),  # noqa: B008
) -> AdminServerFormResponse:
    server_data = await servers_service.update_server(server_id=server_id, data=data)
    if not server_data:
        raise app_exceptions.Error404()

    return AdminServerFormResponse.from_domain(data=server_data)
