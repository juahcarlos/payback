import json
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from typing import Any

from app.core.logs import log
from app.domain.base import BaseDomainModel
from app.utils.datetime import utc_timestamp


@dataclass
class UserServerData:
    cn: str
    expires: int
    password: str
    as_json: str = ""


@dataclass
class ServerHosterData:
    name: str | None = None
    link: str | None = None
    next_payment_date: date | None = None

    def __post_init__(self):
        if isinstance(self.next_payment_date, str):
            self.next_payment_date = datetime.fromisoformat(self.next_payment_date).date()


@dataclass
class FullServerData(BaseDomainModel):
    id: int
    server: str
    enabled: bool
    hidden: bool
    country: str
    city: str
    ip: str
    remote_ips: str | None
    created: int
    hoster_data: ServerHosterData
    users_count: int = 0
    load: int = 0
    traffic_today: int = 0
    traffic_month: int = 0
    errors: list[str] = field(default_factory=list)

    def __post_init__(self):
        if isinstance(self.created, str):
            self.created = utc_timestamp(
                datetime.strptime(self.created, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=UTC
                )
            )

        if isinstance(self.hoster_data, str):
            hoster_data = ServerHosterData()
            try:
                hoster_data = ServerHosterData(**json.loads(self.hoster_data))
            except Exception as exc:  # noqa: BLE001
                log.error("FullServerData: cannot decode hoster_data (%s)", exc)

            self.hoster_data = hoster_data


@dataclass
class ServersStatModel(BaseDomainModel):
    total: int
    online: int
    offline: int
    overdue_payments: int
    average_load: int = 0
    errors: int = 0
    overloaded: int = 0


@dataclass
class ServerBaseFullModel(BaseDomainModel):
    iso: str
    ip: str
    server: str
    enabled: bool
    hidden: bool
    auto_visibility: bool
    country: str
    city: str
    remote_ips: str
    trial: bool
    openvpn: bool
    ikev2: bool
    proxy: bool
    l2tp: bool
    l2tp_raw: bool
    l2tp_ipsec: bool
    sstp: bool
    softether: bool
    hoster_data: ServerHosterData

    def __post_init__(self):
        if isinstance(self.hoster_data, str):
            hoster_data = ServerHosterData()
            try:
                hoster_data = ServerHosterData(**json.loads(self.hoster_data))
            except Exception as exc:  # noqa: BLE001
                log.error("ServerBaseFullModel: cannot decode hoster_data (%s)", exc)

            self.hoster_data = hoster_data


@dataclass
class ServerCreateModel(ServerBaseFullModel):
    pass


@dataclass
class ServerUpdateModel(ServerCreateModel):
    pass


@dataclass
class ServerReadModel(ServerCreateModel):
    id: int


@dataclass
class ServerBaseModel(BaseDomainModel):
    iso: str
    ip: str
    server: str
    enabled: int | bool = True
    hidden: int | bool = False
    auto_visibility: int | bool = True
    country: str | None = None
    city: str | None = None
    remote_ips: str = ""
    trial: int | bool = False
    openvpn: int | bool = False
    ikev2: int | bool = False
    proxy: int | bool = False
    l2tp: int | bool = False
    l2tp_raw: int | bool = False
    l2tp_ipsec: int | bool = False
    sstp: int | bool = False
    softether: int | bool = False


@dataclass
class ServerCreatedReadModel(ServerBaseModel):
    id: int | None = None
    created: datetime | None = None

    def __post_init__(self):
        if isinstance(self.created, str):
            self.created = utc_timestamp(
                datetime.strptime(self.created, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=UTC
                )
            )


@dataclass
class ServerStatReadModel(BaseDomainModel):
    id: int
    server: str
    created: datetime
    online_vpn: int | None
    online_proxy: int | None
    traf_today: int
    traf_yesterday: int
    traf_month: int
    online_l2tp: int | None
    online_sstp: int | None
    online_softether_native: int | None
    wman_version: str | None = None
    bandwidth_today: str | None = None
    bandwidth_yesterday: str | None = None
    bandwidth_month: str | None = None
    load_cpu: str | None = None


@dataclass
class ServerConfigModel(ServerCreatedReadModel):
    hostname: str | None = None
    l2tp_ipsec_preshared_key: str = "saveyourprivacy"


@dataclass
class ServerConfigFileModel:
    country_name: str | None = None
    hosts: list[dict[str, Any]] = field(default_factory=list)
    remote_ips: list[str] = field(default_factory=list)


@dataclass
class ServerCountry(BaseDomainModel):
    name: str
