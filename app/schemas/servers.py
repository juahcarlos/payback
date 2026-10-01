import json
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from time import time
from typing import Self

from pydantic import BaseModel, Field, model_validator

from app.core.config import settings
from app.core.logs import log
from app.domain.servers import FullServerData, ServerReadModel


class AdminServersQueryParams(BaseModel):
    country: str | None = None
    ip: str | None = None


class ServerIPs(BaseModel):
    main: str
    additional: str


class ServerTraffic(BaseModel):
    today: int
    month: int


class ServerError(BaseModel):
    error: str


class NextPaymentState(StrEnum):
    OK = "ok"
    SOON = "soon"
    OVERDUE = "overdue"


class AdminServerResponse(BaseModel):
    id: int
    location: str
    url: str
    ip: ServerIPs
    users: int
    load: int
    traffic: ServerTraffic
    is_online: bool
    visible: bool
    sync: bool
    hoster_name: str | None = None
    hoster_link: str | None = None
    next_payment_date: str | None = None
    next_payment_state: NextPaymentState | None = None
    errors: list[ServerError] = Field(default_factory=list)

    @classmethod
    def from_domain(cls, data: FullServerData) -> Self:
        additional_ip = ""
        if data.remote_ips:
            try:
                remote_ips_data = json.loads(data.remote_ips)
            except Exception as exc:  # noqa: BLE001
                log.warning("AdminServerResponse: cannot decode remote_ips (%s)", exc)
                remote_ips_data = None

            if remote_ips_data and isinstance(remote_ips_data, list):
                additional_ip = remote_ips_data[0]

        is_online = bool(int(time()) - data.created > settings.stat_interval)

        date_today = datetime.now(tz=UTC).date()
        date_week_future = date_today + timedelta(days=7)
        next_payment_state = None
        next_payment_date = data.hoster_data.next_payment_date
        if next_payment_date:
            if next_payment_date <= date_today:
                next_payment_state = NextPaymentState.OVERDUE

            if date_today < next_payment_date <= date_week_future:
                next_payment_state = NextPaymentState.SOON

            if next_payment_date > date_week_future:
                next_payment_state = NextPaymentState.OK

        return cls(
            id=data.id,
            location=f"{data.country}, {data.city}",
            url=f"{data.server}v.{settings.server_domain}",
            ip=ServerIPs(
                main=data.ip,
                additional=additional_ip,
            ),
            next_payment_date=next_payment_date.isoformat() if next_payment_date else None,
            next_payment_state=next_payment_state,
            users=data.users_count,
            load=data.load,
            traffic=ServerTraffic(
                today=data.traffic_today,
                month=data.traffic_month,
            ),
            hoster_name=data.hoster_data.name,
            hoster_link=data.hoster_data.link,
            is_online=is_online,
            visible=not data.hidden,
            sync=data.enabled,
            errors=[ServerError(error=e) for e in data.errors],
        )


class AdminServersResponse(BaseModel):
    servers: list[AdminServerResponse]

    @classmethod
    def from_domain(cls, servers: list[FullServerData]) -> Self:
        return cls(servers=[AdminServerResponse.from_domain(s) for s in servers])


class AdminServerStatsResponse(BaseModel):
    total_servers: int = 0
    online_servers: int = 0
    offline_servers: int = 0
    server_errors: int = 0
    average_load: int = 0
    overloaded_servers: int = 0
    overdue_payments: int = 0
    active_users: int = 0


class AdminServerCountriesResponse(BaseModel):
    data: list[str]


class AdminServerUpdate(BaseModel):
    next_payment: date


class AdminServerFormBase(BaseModel):
    name: str
    iso: str
    country: str
    city: str
    main_ip: str
    additional_ip: str
    trial: bool
    openvpn: bool
    ikev2: bool
    proxy: bool
    l2tp: bool
    l2tp_raw: bool
    l2tp_ipsec: bool
    sstp: bool
    softether: bool
    sync: bool
    visible: bool
    auto_visible: bool
    hoster_name: str | None = None
    hoster_link: str | None = None
    next_payment_date: date | None = None


class AdminServerFormResponse(AdminServerFormBase):
    @classmethod
    def from_domain(cls, data: ServerReadModel) -> Self:
        additional_ip = ""
        remote_ips_data = json.loads(data.remote_ips)
        if remote_ips_data and isinstance(remote_ips_data, list):
            additional_ip = remote_ips_data[0]

        return cls(
            name=data.server,
            iso=data.iso,
            country=data.country,
            city=data.city,
            main_ip=data.ip,
            additional_ip=additional_ip,
            trial=data.trial,
            openvpn=bool(data.openvpn),
            ikev2=bool(data.ikev2),
            proxy=bool(data.proxy),
            l2tp=bool(data.l2tp),
            l2tp_raw=bool(data.l2tp_raw),
            l2tp_ipsec=bool(data.l2tp_ipsec),
            sstp=bool(data.sstp),
            softether=bool(data.softether),
            sync=data.enabled,
            visible=not data.hidden,
            auto_visible=data.auto_visibility,
            hoster_name=data.hoster_data.name,
            hoster_link=data.hoster_data.link,
            next_payment_date=data.hoster_data.next_payment_date,
        )


class AdminServerCreateRequest(AdminServerFormBase):
    name: str = Field(min_length=3, max_length=4)
    iso: str = Field(min_length=2, max_length=2)
    sync: bool = True
    visible: bool = True
    auto_visible: bool = True

    @model_validator(mode='after')
    def check_name_and_iso(self) -> Self:
        if not self.name.startswith(self.iso):
            raise ValueError('Server name should start with iso')

        return self


class AdminServerUpdateRequest(AdminServerCreateRequest):
    pass


class AdminServerPatchRequest(BaseModel):
    sync: bool | None = None
    visible: bool | None = None
