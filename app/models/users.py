from datetime import datetime

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
from sqlalchemy.orm import Mapped, mapped_column

from app.utils.datetime import utc_now_naive

from .base import Base


class Certs(Base):
    __tablename__ = "certs"

    username: Mapped[str] = mapped_column(String(64), primary_key=True)
    ca: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)
    cert: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)
    key: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)
    tls: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)


class Users(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    email: Mapped[str] = mapped_column(VARCHAR(250), default="", nullable=False)
    created: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now_naive, nullable=False)
    cn: Mapped[str | None] = mapped_column(String(100), default=None, nullable=True)
    trial: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    version_page: Mapped[int | None] = mapped_column(Integer, default=0, nullable=True)
    code: Mapped[str | None] = mapped_column(String(250), default=None, nullable=True)
    coupon: Mapped[str | None] = mapped_column(String(250), default=None, nullable=True)
    expires: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True)
    plan: Mapped[int | None] = mapped_column(Integer, default=None, nullable=True)
    country_iso: Mapped[str | None] = mapped_column(String(2), default="-", nullable=True)
    password: Mapped[str | None] = mapped_column(String(100), default="", nullable=True)
    reg_source: Mapped[str | None] = mapped_column(String(100), default="web", nullable=True)
    dubious: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    subscribed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lang: Mapped[str] = mapped_column(String(2), default="en", nullable=False)
    partner_id: Mapped[int | None] = mapped_column(BigInteger, default=None, nullable=True)
    note: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)

    __table_args__ = (
        Index('id', "id", unique=True),
        Index('users_email_unique', "email", unique=True),
        Index('users_code_unique', "code", unique=True),
        Index('users_cn_unique', "cn", unique=True),
        Index('users_code_expires', "code", "expires"),
        Index('users_trial', "trial"),
        Index('users_dubious', "dubious"),
        Index('users_expires', "expires", mysql_using='BTREE'),
        Index('users_created', "created"),
        Index('trial_expires', "trial", "expires"),
    )


class Partners(Base):
    __tablename__ = "partners"

    id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    created: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now_naive, nullable=False)
    password: Mapped[str | None] = mapped_column(VARCHAR(100), default=None, nullable=True)
    commission: Mapped[int | None] = mapped_column(BigInteger, default=None, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)
    lang: Mapped[str] = mapped_column(VARCHAR(2), default="en", nullable=False)

    __table_args__ = (
        Index('id', "id", unique=True),
    )
