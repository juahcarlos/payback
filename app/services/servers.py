import asyncio
import json
import re
from dataclasses import asdict
from datetime import UTC, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import httpx
from fastapi import Depends

from app.core.config import settings
from app.core.locale import get_current_locale
from app.core.logs import log
from app.domain.servers import (
    FullServerData,
    ServerConfigFileModel,
    ServerConfigModel,
    ServerCreatedReadModel,
    ServerCreateModel,
    ServerHosterData,
    ServerReadModel,
    ServersStatModel,
    ServerUpdateModel,
    UserServerData,
)
from app.repositories import (
    ServerDBRepo,
    get_server_repo,
)
from app.schemas import (
    AdminServerCreateRequest,
    AdminServerPatchRequest,
    AdminServersQueryParams,
    AdminServerUpdateRequest,
)
from app.services.ips import (
    IPInfoService,
    get_ipinfo_service,
)
from app.services.translation import (
    TranslationService,
    get_translation_service,
)
from app.utils.datetime import utc_timestamp


class ServerType(StrEnum):
    OPENVPN = "openvpn"
    L2TP = "l2tp"
    SSTP = "sstp"
    SOFTETHER = "softether"


class UpdateServerException(Exception):
    def __init__(self, message, server_ip, server_id):
        super().__init__(message)
        self.server = f"{server_id}_{server_ip}"


class ServerUpdateService:
    TIMEOUT: int = 1
    HEADERS: MappingProxyType = MappingProxyType({
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
    })

    def __init__(self, repo: ServerDBRepo) -> None:
        self.repo = repo

    @staticmethod
    async def httpx_post(url: str, data: str, client: httpx.AsyncClient) -> None:
        try:
            response = await client.post(
                url,
                params={"auth": settings.server_secret_key},
                content=data,
            )
            response.raise_for_status()
        except Exception as exc:
            log.error("Servers update error: httpx_post - %s", exc)
            raise

    async def post_update_server(
            self,
            server: ServerCreatedReadModel,
            user_data: UserServerData,
            client: httpx.AsyncClient,
    ) -> None:
        url = f"https://{server.server}v.secwhapi.net:55555/update"
        await self.httpx_post(
            url=url,
            data=user_data.as_json,
            client=client,
        )

    async def post_update_softether(
            self,
            server: ServerCreatedReadModel,
            user_data: UserServerData,
            client: httpx.AsyncClient,
    ) -> None:
        url = f"https://{server.server}v.secwhapi.net:55555/update"

        cn = user_data.cn
        password = user_data.password
        id_ = int(re.sub("sec|cn", "", cn))
        request_data = {
            "params": {
                "HubName_str": "default",
                "Auth_Password_str": password,
                "AuthType_u32": 1,
                "Name_str": cn
            },
            "jsonrpc": "2.0",
            "method": "CreateUser",
            "id": id_,
        }

        await self.httpx_post(
            url=url,
            data=json.dumps(request_data),
            client=client,
        )

    async def post_url(
            self,
            server: ServerCreatedReadModel,
            user_data: UserServerData,
    ) -> None:
        # Private server CAs must be installed in the runtime trust store.
        async with httpx.AsyncClient(
                headers=self.HEADERS,
                timeout=self.TIMEOUT,
        ) as client:
            try:
                await self.post_update_server(server, user_data, client)
            except Exception as exc:
                raise UpdateServerException(
                    f"Couldn't update server ({exc})",
                    server_ip=server.ip, server_id=server.id,
                ) from exc

            if server.sstp or server.softether:
                try:
                    await self.post_update_softether(server, user_data, client)
                except Exception as exc:
                    raise UpdateServerException(
                        f"Couldn't update softether server ({exc})",
                        server_ip=server.ip, server_id=server.id,
                    ) from exc

    async def servers_update(
            self,
            user_data: UserServerData,
    ) -> None:
        if not settings.prod:
            log.info("ServerUpdateService: skipping servers update in stage environment")
            return

        data = json.dumps({
            user_data.cn: {
                "expires": user_data.expires,
                "password": user_data.password,
            }
        })
        user_data.as_json = data

        tasks = []
        servers_enabled_db = await self.repo.get_enabled_servers()
        for server in servers_enabled_db:
            task = asyncio.create_task(self.post_url(server, user_data))
            tasks.append(task)

        errors = 0
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, UpdateServerException):
                log.error(
                    "ServerUpdateService: "
                    "Error occured during server update (%s)",
                    res.server
                )
                errors += 1

        log.info("ServerUpdateService: servers updated (%d/%d)", len(tasks) - errors, len(tasks))


def get_server_update_service(
        repo: ServerDBRepo = Depends(get_server_repo),  # noqa: B008
) -> ServerUpdateService:
    return ServerUpdateService(repo=repo)


class ServerService:
    def __init__(
            self,
            repo: ServerDBRepo,
            ipinfo_service: IPInfoService,
            translation_service: TranslationService,
            locale: str,
    ) -> None:
        self.repo = repo
        self.ipinfo_service = ipinfo_service
        self.translation_service = translation_service
        self.locale = locale

    @staticmethod
    def get_vpn_proxy_host(server_data: ServerConfigModel) -> dict[str, Any]:
        return {
            "city": server_data.city,
            "host": server_data.ip,
            "port": "8888",
        }

    @staticmethod
    def get_vpn_openvpn_host(server_data: ServerConfigModel) -> dict[str, Any]:
        return {
            "city": server_data.city,
            "host": server_data.ip,
            "port": "443",
        }

    @staticmethod
    def get_vpn_l2tp_host(server_data: ServerConfigModel) -> dict[str, Any]:
        return {
            "city": server_data.city,
            "host": server_data.hostname,
            "ip": server_data.ip,
            "ipsec": str(server_data.l2tp_ipsec),
            "ipsec_preshared_key": server_data.l2tp_ipsec_preshared_key,
            "raw": str(server_data.l2tp_raw),
        }

    @staticmethod
    def get_vpn_ikev2_host(server_data: ServerConfigModel) -> dict[str, Any]:
        return {
            "city": server_data.city,
            "host": server_data.hostname,
        }

    @staticmethod
    def get_vpn_softether_host(server_data: ServerConfigModel) -> dict[str, Any]:
        return {
            "city": server_data.city,
            "host": server_data.hostname,
            "ip": server_data.ip,
            "port": "443",
        }

    @staticmethod
    def get_vpn_sstp_host(server_data: ServerConfigModel) -> dict[str, Any]:
        return {
            "city": server_data.city,
            "host": server_data.hostname,
            "ip": server_data.ip,
            "port": "443",
        }

    def get_host_data_by_server_type(
            self,
            server_type: str,
            server_data: ServerConfigModel,
    ) -> dict[str, Any] | None:
        if not getattr(server_data, server_type, False):
            return None

        get_callable = {
            "proxy": self.get_vpn_proxy_host,
            "openvpn": self.get_vpn_openvpn_host,
            "l2tp": self.get_vpn_l2tp_host,
            "ikev2": self.get_vpn_ikev2_host,
            "softether": self.get_vpn_softether_host,
            "sstp": self.get_vpn_sstp_host,
        }.get(server_type)

        if not get_callable:
            return None

        return get_callable(server_data)

    @staticmethod
    def _check_server(server: ServerCreatedReadModel, trial: bool) -> bool:
        if (
                (trial and not server.trial)
                or not server.created
        ):
            return False

        server_stat_time = utc_timestamp(server.created)
        current_time = utc_timestamp(datetime.now(UTC))
        if current_time - server_stat_time > settings.stat_interval:
            return False

        return True

    async def get_server_load(self, server_name: str) -> str:
        stat = await self.repo.get_latest_server_stat_by_name(server_name)
        if not stat:
            return "0"

        load = stat.traf_today / 1000
        if load == 0.0:
            load = int(load)

        return str(load)

    async def get_server_form_data_by_id(self, server_id: int) -> ServerReadModel | None:
        return await self.repo.get_server_by_id(server_id=server_id)

    async def get_active_servers_data(  # TODO: refactor!
            self,
            server_type: str,
            trial: bool = False,
    ) -> dict[str, ServerConfigFileModel]:
        user_servers: dict[str, ServerConfigFileModel] = {}
        active_servers = await self.repo.get_enabled_servers()
        for server_from_db in active_servers:
            if not self._check_server(server_from_db, trial):
                continue

            server_data = ServerConfigModel(
                hostname=f"{server_from_db.server}v.secwhapi.net",
                **asdict(server_from_db),
            )

            server_config = ServerConfigFileModel()

            server_config.country_name = server_from_db.country
            iso = server_from_db.iso
            if iso:
                server_config.country_name = self.translation_service.translate_message(
                    f'country.{iso}',
                )

            host_data = self.get_host_data_by_server_type(server_type, server_data)
            if not host_data:
                continue

            if iso not in user_servers:
                user_servers[iso] = server_config

            server_load = await self.get_server_load(server_data.server)
            host_data.update({"load": server_load})

            city = self.translation_service.translate_message(
                key=f'city.{host_data["city"]}',
                locale=self.locale,
            ) or "Unknown"
            host_data["city"] = city.encode('utf-8').decode()

            coordinates = self.ipinfo_service.get_coordinates(server_data.ip)
            host_data["coordinates"] = asdict(coordinates)

            host_data = dict(sorted(host_data.items()))
            user_servers[iso].hosts.append(host_data)
            user_servers[iso].remote_ips.append(host_data["host"])

        servers = dict(sorted(user_servers.items()))

        return servers

    async def get_servers_data_for_configs(
            self,
            server_type: ServerType,
            trial: bool,
    ) -> list[ServerConfigModel]:
        servers_data = []
        active_servers = await self.repo.get_enabled_servers_by_type(server_type=server_type)
        for server_from_db in active_servers:
            if not self._check_server(server_from_db, trial):
                continue

            server_data = ServerConfigModel(
                hostname=f"{server_from_db.server}v.secwhapi.net",
                **asdict(server_from_db),
            )
            servers_data.append(server_data)

        return servers_data

    async def get_full_servers_data(
            self,
            filters: AdminServersQueryParams,
    ) -> list[FullServerData]:
        filters_data = {}
        if filters.country:
            filters_data["country"] = filters.country

        if filters.ip:
            filters_data["ip"] = filters.ip

        return await self.repo.get_servers_with_filters(filters=filters_data)

    async def get_servers_stat(self) -> ServersStatModel | None:
        return await self.repo.get_servers_stat()

    async def get_server_countries(self) -> list[str]:
        data = await self.repo.get_server_countries()
        return sorted({d.name for d in data})

    async def update_server(
            self,
            server_id: int,
            data: AdminServerUpdateRequest,
    ) -> ServerReadModel | None:
        if not await self.repo.get_server_by_id(server_id):
            return None

        await self.repo.update_server(
            server_id=server_id,
            data=asdict(
                ServerUpdateModel(
                    iso=data.iso,
                    ip=data.main_ip,
                    server=data.name,
                    enabled=data.sync,
                    hidden=not data.visible,
                    auto_visibility=data.auto_visible,
                    country=data.country,
                    city=data.city,
                    remote_ips=json.dumps([data.additional_ip]),
                    trial=data.trial,
                    openvpn=data.openvpn,
                    ikev2=data.ikev2,
                    proxy=data.proxy,
                    l2tp=data.l2tp,
                    l2tp_raw=data.l2tp_raw,
                    l2tp_ipsec=data.l2tp_ipsec,
                    sstp=data.sstp,
                    softether=data.softether,
                    hoster_data=ServerHosterData(
                        name=data.hoster_name,
                        link=data.hoster_link,
                        next_payment_date=data.next_payment_date,
                    ),
                ),
            )
        )

        return await self.get_server_form_data_by_id(server_id=server_id)

    async def partially_update_server(self, server_id: int, data: AdminServerPatchRequest) -> None:
        data_to_update = {}

        if data.visible is not None:
            data_to_update["hidden"] = not data.visible

        if data.sync is not None:
            data_to_update["enabled"] = data.sync

        await self.repo.update_server(server_id=server_id, data=data_to_update)

    async def create_server(
            self,
            server_data: AdminServerCreateRequest,
    ) -> ServerReadModel | None:
        data = ServerCreateModel(
            server=server_data.name,
            enabled=server_data.sync,
            hidden=not server_data.visible,
            auto_visibility=server_data.auto_visible,
            iso=server_data.iso,
            country=server_data.country,
            city=server_data.city,
            ip=server_data.main_ip,
            remote_ips=json.dumps([server_data.additional_ip]),
            trial=server_data.trial,
            openvpn=server_data.openvpn,
            ikev2=server_data.ikev2,
            proxy=server_data.proxy,
            l2tp=server_data.l2tp,
            l2tp_raw=server_data.l2tp_raw,
            l2tp_ipsec=server_data.l2tp_ipsec,
            sstp=server_data.sstp,
            softether=server_data.softether,
            hoster_data=ServerHosterData(
                name=server_data.hoster_name,
                link=server_data.hoster_link,
                next_payment_date=server_data.next_payment_date,
            ),
        )

        await self.repo.create_server(data=asdict(data))

        server = await self.repo.get_server_by_name(server_data.name)
        if server and server.id:
            return await self.get_server_form_data_by_id(server_id=server.id)

        return None


def get_server_service(
        repo: ServerDBRepo = Depends(get_server_repo),  # noqa: B008
        ipinfo_service: IPInfoService = Depends(get_ipinfo_service),  # noqa: B008
        translation_service: TranslationService = Depends(get_translation_service),  # noqa: B008
        locale: str = Depends(get_current_locale),
) -> ServerService:
    return ServerService(
        repo=repo,
        ipinfo_service=ipinfo_service,
        translation_service=translation_service,
        locale=locale,
    )
