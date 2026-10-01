from typing import Callable

from httpx import AsyncClient

from app.domain.servers import ServersStatModel, FullServerData
from app.domain.users import UserCountModel
from app.services import get_server_service, get_user_service
from app.schemas import (
    AdminServersQueryParams,
    AdminServerResponse,
    AdminServerFormResponse,
)
from app.utils.auth import verify_basic_auth


BASE_SERVERS_ROUTE = "/admin/servers"


async def test_servers(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_server_service: Callable,
        mock_servers_data: list[FullServerData],
        mock_servers_params: AdminServersQueryParams,
        mock_verify_auth,
) -> None:
    override_depends(get_server_service, mock_get_server_service)
    override_depends(verify_basic_auth, mock_verify_auth)

    response = await async_client.get(
        BASE_SERVERS_ROUTE,
        params=mock_servers_params.model_dump(),
    )

    expected_response = {
        "servers": [AdminServerResponse.from_domain(d).model_dump() for d in mock_servers_data],
    }

    assert response.status_code == 200
    assert response.json() == expected_response


async def test_server_countries(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_server_service: Callable,
        mock_countries: list[str],
        mock_verify_auth,
) -> None:
    override_depends(get_server_service, mock_get_server_service)
    override_depends(verify_basic_auth, mock_verify_auth)

    response = await async_client.get(
        f"{BASE_SERVERS_ROUTE}/countries",
    )

    assert response.status_code == 200
    assert response.json() == {"data": mock_countries}


async def test_server_stats(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_server_service: Callable,
        mock_get_user_service: Callable,
        mock_servers_stat: ServersStatModel,
        mock_user_count: UserCountModel,
        mock_verify_auth,
) -> None:
    override_depends(get_server_service, mock_get_server_service)
    override_depends(get_user_service, mock_get_user_service)
    override_depends(verify_basic_auth, mock_verify_auth)

    response = await async_client.get(
        f"{BASE_SERVERS_ROUTE}/stats",
    )

    expected_response = {
        "total_servers": mock_servers_stat.total,
        "online_servers": mock_servers_stat.online,
        "offline_servers": mock_servers_stat.offline,
        "server_errors": mock_servers_stat.errors,
        "average_load": mock_servers_stat.average_load,
        "overloaded_servers": mock_servers_stat.overloaded,
        "overdue_payments": mock_servers_stat.overdue_payments,
        "active_users": mock_user_count.active,
    }

    assert response.status_code == 200
    assert response.json() == expected_response


async def test_get_server(
        override_depends: Callable,
        async_client: AsyncClient,
        mock_get_server_service: Callable,
        mock_server_data,
        mock_verify_auth,
) -> None:
    override_depends(get_server_service, mock_get_server_service)
    override_depends(verify_basic_auth, mock_verify_auth)

    response = await async_client.get(
        f"{BASE_SERVERS_ROUTE}/1",
    )

    expected_response = AdminServerFormResponse.from_domain(mock_server_data).model_dump()

    assert response.status_code == 200
    assert response.json() == expected_response
