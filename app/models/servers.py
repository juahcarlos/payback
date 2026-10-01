from datetime import datetime
from typing import Any

from sqlalchemy import (
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.datetime import utc_now_naive

from .base import Base


class ServersConfig(Base):
    __tablename__ = "servers_config"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    server: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hidden: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auto_visibility: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    iso: Mapped[str | None] = mapped_column(VARCHAR(2), default='-', nullable=True)
    country: Mapped[str | None] = mapped_column(VARCHAR(50), default="", nullable=True)
    city: Mapped[str | None] = mapped_column(VARCHAR(50), default="", nullable=True)
    ip: Mapped[str | None] = mapped_column(VARCHAR(15), default="", nullable=True)
    remote_ips: Mapped[str | None] = mapped_column(Text, default="", nullable=True)
    trial: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    openvpn: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    ikev2: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    proxy: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    l2tp: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    l2tp_raw: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    l2tp_ipsec: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    sstp: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    softether: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    hoster_data: Mapped[dict[str, Any] | None] = mapped_column(MutableDict.as_mutable(JSON))

    __table_args__ = (Index('server', "server", unique=True),)


class VpnServersStat(Base):
    __tablename__ = "vpn_servers_stat"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    server: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    created: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now_naive, nullable=False)
    online_vpn: Mapped[int] = mapped_column(Integer, nullable=False)
    online_proxy: Mapped[int | None] = mapped_column(Integer)
    traf_today: Mapped[int] = mapped_column(Integer, nullable=False)
    traf_yesterday: Mapped[int] = mapped_column(Integer, nullable=False)
    traf_month: Mapped[int] = mapped_column(Integer, nullable=False)
    online_l2tp: Mapped[int | None] = mapped_column(Integer)
    online_sstp: Mapped[int | None] = mapped_column(Integer)
    online_softether_native: Mapped[int | None] = mapped_column(Integer)
    wman_version: Mapped[str | None] = mapped_column(String(64), default="", nullable=True)
    bandwidth_today: Mapped[str | None] = mapped_column(String(64), default="", nullable=True)
    bandwidth_yesterday: Mapped[str | None] = mapped_column(String(64), default="", nullable=True)
    bandwidth_month: Mapped[str | None] = mapped_column(String(64), default="", nullable=True)
    load_cpu: Mapped[str | None] = mapped_column(String(64), default="0", nullable=True)

    __table_args__ = (Index("ix_vpn_servers_stat_server_created", "server", "created"),)
