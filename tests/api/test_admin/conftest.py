from datetime import datetime
from typing import Callable

import pytest

from app.domain.servers import ServersStatModel, FullServerData, ServerHosterData, ServerReadModel
from app.domain.users import UserCountModel
from app.schemas import AdminServersQueryParams


@pytest.fixture()
def mock_servers_params() -> AdminServersQueryParams:
    return AdminServersQueryParams(country="Russia")


@pytest.fixture()
def mock_countries() -> list[str]:
    return ["Russia", "France", "Germany"]


@pytest.fixture()
def mock_servers_stat() -> ServersStatModel:
    return ServersStatModel(
        total=30,
        online=20,
        offline=10,
        overdue_payments=2,
        average_load=50,
        errors=1,
        overloaded=2,
    )


@pytest.fixture()
def mock_servers_data() -> list[FullServerData]:
    return [
        FullServerData(
            id=1,
            server="ru",
            enabled=True,
            hidden=False,
            country="Russia",
            city="Omsk",
            ip="111.222.333.444",
            remote_ips='["111.222.333.445"]',
            created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hoster_data=ServerHosterData(name="Hoster", link="example.com", next_payment_date="2026-10-09"),
        ),
        FullServerData(
            id=2,
            server="ru",
            enabled=True,
            hidden=False,
            country="Russia",
            city="Tomsk",
            ip="111.222.333.555",
            remote_ips='["111.222.333.556"]',
            created=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            hoster_data=ServerHosterData(),
        ),
    ]


@pytest.fixture()
def mock_server_data() -> ServerReadModel:
    return ServerReadModel(
        id=2,
        server="ru1",
        enabled=True,
        hidden=False,
        country="Russia",
        city="Tomsk",
        ip="111.222.333.555",
        remote_ips='["111.222.333.556"]',
        iso="ru",
        auto_visibility=True,
        trial=False,
        openvpn=True,
        ikev2=True,
        proxy=True,
        l2tp=True,
        l2tp_raw=True,
        l2tp_ipsec=True,
        sstp=True,
        softether=True,
        hoster_data=ServerHosterData(),
    )


@pytest.fixture()
def mock_get_server_service(
        mock_countries: list[str],
        mock_servers_stat: ServersStatModel,
        mock_servers_data: list[FullServerData],
        mock_server_data: ServerReadModel,
) -> Callable:
    class MockServerService:
        async def get_server_countries(self) -> list[str]:
            return mock_countries

        async def get_servers_stat(self) -> ServersStatModel:
            return mock_servers_stat

        async def get_full_servers_data(self, filters) -> list[FullServerData]:
            return mock_servers_data

        async def get_server_form_data_by_id(self, server_id) -> ServerReadModel:
            return mock_server_data

    def get_mock_server_service() -> MockServerService:
        return MockServerService()

    return get_mock_server_service


@pytest.fixture()
def mock_user_count() -> UserCountModel:
    return UserCountModel(active=10)


@pytest.fixture()
def mock_get_user_service(mock_user_count: UserCountModel) -> Callable:
    class MockUserService:
        async def get_users_count(self) -> UserCountModel:
            return mock_user_count

    def get_mock_user_service() -> MockUserService:
        return MockUserService()

    return get_mock_user_service


@pytest.fixture()
def mock_verify_auth():
    def mock_verify():
        return None

    return mock_verify
