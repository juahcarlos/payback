from datetime import UTC, datetime
from time import time
from typing import Any

from sqlalchemy import DECIMAL, Date, Integer, cast, insert, select, update
from sqlalchemy.sql import case, func, or_

from app.core.config import settings
from app.domain.servers import (
    FullServerData,
    ServerCountry,
    ServerCreatedReadModel,
    ServerReadModel,
    ServersStatModel,
    ServerStatReadModel,
)
from app.models import ServersConfig, VpnServersStat
from app.utils.datetime import as_utc_naive

from .base import BaseDBRepo


class ServerDBRepo(BaseDBRepo):
    OVERLOADED_THRESHOLD = 0.85

    # CREATE

    async def create_server(self, data: dict[str, Any]) -> None:
        statement = insert(ServersConfig).values(**data)
        await self.insert_only(statement)

    # READ

    async def get_server_by_id(self, server_id: int) -> ServerReadModel | None:
        statement = select(ServersConfig).filter_by(id=server_id)
        return await self.select_one(statement, ServerReadModel)

    async def get_server_countries(self) -> list[ServerCountry]:
        statement = (
            select(ServersConfig.country.label("name"))
            .filter(ServersConfig.enabled == 1)
            .filter(ServersConfig.hidden == 0)
        )

        return await self.select_many(statement, ServerCountry)

    async def get_server_by_name(self, server_name: str) -> ServerReadModel | None:
        statement = select(ServersConfig).filter_by(server=server_name)
        return await self.select_one(statement, ServerReadModel)

    async def get_servers_stat(self) -> ServersStatModel | None:
        latest_created = (
            select(VpnServersStat.created)
            .where(VpnServersStat.server == ServersConfig.server)
            .order_by(VpnServersStat.created.desc())
            .limit(1)
            .scalar_subquery()
        )
        latest_load = (
            select(VpnServersStat.load_cpu)
            .where(VpnServersStat.server == ServersConfig.server)
            .order_by(VpnServersStat.created.desc())
            .limit(1)
            .scalar_subquery()
        )
        latest_stats_subq = select(
            ServersConfig.id.label("id"),
            ServersConfig.hoster_data.label("hoster_data"),
            latest_created.label("created"),
            latest_load.label("load_cpu"),
        ).subquery()

        date_today = datetime.fromtimestamp(time(), tz=UTC).date()
        active_dt = as_utc_naive(
            datetime.fromtimestamp(time() - settings.stat_interval, tz=UTC)
        )
        statement = (
            select(
                func.count(latest_stats_subq.c.id).label("total"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                or_(
                                    latest_stats_subq.c.created.is_(None),
                                    latest_stats_subq.c.created < active_dt,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("offline"),
                func.coalesce(
                    func.sum(
                        case(
                            (latest_stats_subq.c.created >= active_dt, 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("online"),
                func.coalesce(
                    func.sum(
                        case((
                            cast(
                                latest_stats_subq.c.hoster_data["next_payment_date"].as_string(),
                                Date
                            ) >= date_today,
                            1
                        ), else_=0
                        )
                    ),
                    0,
                ).label("overdue_payments"),
                func.coalesce(
                    cast(
                        func.floor(
                            func.avg(cast(latest_stats_subq.c.load_cpu, DECIMAL(4, 3))) * 100
                        ),
                        Integer,
                    ),
                    0,
                ).label("average_load"),
                func.coalesce(
                    func.sum(
                        (
                            cast(latest_stats_subq.c.load_cpu, DECIMAL(4, 3))
                            > self.OVERLOADED_THRESHOLD
                        ).cast(Integer)
                    ),
                    0,
                ).label("overloaded"),
                # errors,  # ???
            )
            .select_from(latest_stats_subq)
        )

        return await self.select_one(statement, ServersStatModel)

    async def get_servers_with_filters(
            self,
            filters: dict[str, Any] | None = None,
    ) -> list[FullServerData]:
        if filters is None:
            filters = {}

        max_created_subq = (
            select(
                VpnServersStat.server,
                func.max(VpnServersStat.created).label("created"),
            )
            .group_by(VpnServersStat.server)
            .subquery()
        )

        latest_stats_subq = (
            select(
                VpnServersStat.server,
                VpnServersStat.created,
                VpnServersStat.online_vpn,
                VpnServersStat.load_cpu,
                VpnServersStat.traf_today,
                VpnServersStat.traf_month,
            )
            .join(
                max_created_subq,
                (VpnServersStat.server == max_created_subq.c.server) &
                (VpnServersStat.created == max_created_subq.c.created)
            )
            .subquery()
        )

        statement = (
            select(
                ServersConfig.id,
                ServersConfig.server,
                ServersConfig.enabled,
                ServersConfig.hidden,
                ServersConfig.country,
                ServersConfig.city,
                ServersConfig.ip,
                ServersConfig.hoster_data,
                ServersConfig.remote_ips,
                latest_stats_subq.c.created,
                latest_stats_subq.c.online_vpn.label("users_count"),
                latest_stats_subq.c.load_cpu.label("load"),
                latest_stats_subq.c.traf_today.label("traffic_today"),
                latest_stats_subq.c.traf_month.label("traffic_month"),
                cast(
                    func.floor(
                        cast(latest_stats_subq.c.load_cpu, DECIMAL(4, 3)) * 100
                    ),
                    Integer
                ).label("load"),
            )
            .join(
                latest_stats_subq,
                latest_stats_subq.c.server == ServersConfig.server,
            )
        )

        if "country" in filters:
            statement = statement.filter(ServersConfig.country == filters["country"])

        if "ip" in filters:
            statement = statement.filter(ServersConfig.ip.contains(filters["ip"]))

        return await self.select_many(statement, FullServerData)

    async def get_full_server_by_id(self, server_id: int) -> FullServerData | None:
        latest_created_subq = (
            select(
                VpnServersStat.server,
                func.max(VpnServersStat.created).label("created"),
            )
            .group_by(VpnServersStat.server)
            .subquery()
        )
        statement = (
            select(
                ServersConfig.id,
                ServersConfig.server,
                ServersConfig.enabled,
                ServersConfig.country,
                ServersConfig.city,
                ServersConfig.ip,
                ServersConfig.hoster_data,
                ServersConfig.remote_ips,
                # users_count,
                # load_day,
                # load_week,
                # load_month,
                latest_created_subq.c.created,
            )
            .join(
                latest_created_subq,
                latest_created_subq.c.server == ServersConfig.server,
            )
            .filter(ServersConfig.id == server_id)
        )

        return await self.select_one(statement, FullServerData)


    async def get_enabled_servers(self) -> list[ServerCreatedReadModel]:
        latest_created_subq = (
            select(
                VpnServersStat.server,
                func.max(VpnServersStat.created).label("created"),
            )
            .group_by(VpnServersStat.server)
            .subquery()
        )
        statement = (
            select(
                ServersConfig.id,
                ServersConfig.iso,
                ServersConfig.ip,
                ServersConfig.server,
                ServersConfig.enabled,
                ServersConfig.hidden,
                ServersConfig.auto_visibility,
                ServersConfig.country,
                ServersConfig.city,
                ServersConfig.remote_ips,
                ServersConfig.trial,
                ServersConfig.openvpn,
                ServersConfig.ikev2,
                ServersConfig.proxy,
                ServersConfig.l2tp,
                ServersConfig.l2tp_raw,
                ServersConfig.l2tp_ipsec,
                ServersConfig.sstp,
                ServersConfig.softether,
                latest_created_subq.c.created,
            )
            .join(
                latest_created_subq,
                latest_created_subq.c.server == ServersConfig.server,
            )
            .filter(ServersConfig.enabled == 1)
            .filter(ServersConfig.hidden == 0)
        )

        return await self.select_many(statement, ServerCreatedReadModel)

    async def get_enabled_servers_by_type(
            self,
            server_type: str,
    ) -> list[ServerCreatedReadModel]:
        latest_created_subq = (
            select(
                VpnServersStat.server,
                func.max(VpnServersStat.created).label("created"),
            )
            .group_by(VpnServersStat.server)
            .subquery()
        )
        statement = (
            select(
                ServersConfig.id,
                ServersConfig.iso,
                ServersConfig.ip,
                ServersConfig.server,
                ServersConfig.enabled,
                ServersConfig.hidden,
                ServersConfig.auto_visibility,
                ServersConfig.country,
                ServersConfig.city,
                ServersConfig.remote_ips,
                ServersConfig.trial,
                ServersConfig.openvpn,
                ServersConfig.ikev2,
                ServersConfig.proxy,
                ServersConfig.l2tp,
                ServersConfig.l2tp_raw,
                ServersConfig.l2tp_ipsec,
                ServersConfig.sstp,
                ServersConfig.softether,
                latest_created_subq.c.created,
            )
            .join(
                latest_created_subq,
                latest_created_subq.c.server == ServersConfig.server,
            )
            .filter(ServersConfig.enabled == 1)
            .filter(ServersConfig.hidden == 0)
            .filter(getattr(ServersConfig, server_type).is_(True))
            .order_by(ServersConfig.country.asc())
        )

        return await self.select_many(statement, ServerCreatedReadModel)

    async def get_enabled_servers_without_stats(self) -> list[ServerReadModel]:
        statement = (
            select(ServersConfig)
            .filter_by(enabled=1)
            .filter_by(hidden=0)
        )
        return await self.select_many(statement, ServerReadModel)

    async def get_latest_server_stat_by_name(
            self,
            server_name: str,
    ) -> ServerStatReadModel | None:
        statement = (
            select(VpnServersStat)
            .filter_by(server=server_name)
            .order_by(VpnServersStat.created.desc())
            .limit(1)
        )
        return await self.select_one(statement, ServerStatReadModel)

    # UPDATE

    async def update_server(
            self,
            server_id: int,
            data: dict[str, Any],
    ) -> None:
        statement = (
            update(ServersConfig)
            .where(ServersConfig.id == server_id)
            .values(**data)
        )
        await self.update_only(statement)


def get_server_repo() -> ServerDBRepo:
    return ServerDBRepo()
