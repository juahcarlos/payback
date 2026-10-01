from datetime import UTC, datetime
from decimal import Decimal

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
from sqlalchemy.types import DECIMAL

from app.utils.datetime import utc_now_naive

from .base import Base


class Coupons(Base):
    __tablename__ = "coupons"

    coupon: Mapped[str] = mapped_column(String(250), default="", nullable=False, primary_key=True)
    max_use_limit: Mapped[int | None] = mapped_column(Integer)
    percent: Mapped[int | None] = mapped_column(Integer)
    prolong: Mapped[int | None] = mapped_column(Integer)
    times_used: Mapped[int | None] = mapped_column(Integer)
    manual: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    expiration: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        default=datetime(2038, 1, 19, 3, 14, 7, tzinfo=UTC),
        nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, default=None, nullable=True)
    created: Mapped[datetime | None] = mapped_column(
        TIMESTAMP,
        default=utc_now_naive,
        nullable=True,
    )
    plans: Mapped[str | None] = mapped_column(String(64), default=None, nullable=True)

    __table_args__ = (
        Index('coupons_coupon', "coupon", unique=True),
        Index('manual_created', "manual", "created"),
    )


class BuyFormFilling(Base):
    __tablename__ = "buy_form_filling"

    id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    created: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now_naive, nullable=False)
    email: Mapped[str | None] = mapped_column(VARCHAR(250), default=None, nullable=True)
    lang: Mapped[str] = mapped_column(VARCHAR(2), default=None, nullable=False)

    __table_args__ = (
        Index('created', "created"),
        Index('email', "email"),
    )


class Transactions(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    system: Mapped[str | None] = mapped_column(String(100), default=None, nullable=True)
    data: Mapped[str | None] = mapped_column(Text)
    days: Mapped[int | None] = mapped_column(Integer)
    amount: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    email: Mapped[str | None] = mapped_column(VARCHAR(250), default="", nullable=True)
    expires: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now_naive, nullable=False)
    created: Mapped[datetime] = mapped_column(TIMESTAMP, default=utc_now_naive, nullable=False)
    trial: Mapped[bool | None] = mapped_column(Boolean, default=True, nullable=True)
    coupon: Mapped[str | None] = mapped_column(String(250), default=None, nullable=True)
    version_page: Mapped[int | None] = mapped_column(Integer)
    country_iso: Mapped[str | None] = mapped_column(String(2), default="-", nullable=True)
    complete: Mapped[bool | None] = mapped_column(Boolean, default=False, nullable=True)
    partner_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    partner_id: Mapped[int | None] = mapped_column(BigInteger, default=0, nullable=True)
    partner_referrer_id: Mapped[int | None] = mapped_column(BigInteger, default=0, nullable=True)
    pushed_by: Mapped[str | None] = mapped_column(String(250), default=None, nullable=True)
    remote_amount: Mapped[Decimal | None] = mapped_column(DECIMAL(10, 2))
    check_order_id: Mapped[int | None] = mapped_column(BigInteger, default=0, nullable=True)
    pay_time: Mapped[int | None] = mapped_column(Integer)
    remote_status: Mapped[str | None] = mapped_column(VARCHAR(255), default=None, nullable=True)
    credited: Mapped[str | None] = mapped_column(String(255), default=None, nullable=True)
    json_custom_fields: Mapped[str | None] = mapped_column(String(8000))
    remote_invoice_id: Mapped[str | None] = mapped_column(String(8000))
    refund: Mapped[bool | None] = mapped_column(Boolean, default=0, nullable=True)

    __table_args__ = (
        Index('transactions_email', "email"),
        Index('transactions_email_complete', "email", "complete"),
        Index('transactions_trial', "trial"),
        Index('transactions_created', "created"),
        Index('transactions_expires', "expires"),
        Index('transactions_partner_id', "partner_id"),
        Index('transactions_coupon', "coupon", "created"),
        Index('transactions_complete_created', "complete", "created"),
    )


class TariffsWhox(Base):
    __tablename__ = "tariffs_whox"

    id: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True, primary_key=True)
    month: Mapped[str | None] = mapped_column(VARCHAR(10), default=None, nullable=True)
    count: Mapped[str | None] = mapped_column(VARCHAR(5), default=None, nullable=True)
    economy: Mapped[str | None] = mapped_column(VARCHAR(5), default=None, nullable=True)
    popular: Mapped[str | None] = mapped_column(VARCHAR(5), default=None, nullable=True)
    countTextSum: Mapped[str | None] = mapped_column(VARCHAR(5), default=None, nullable=True)
    date: Mapped[str | None] = mapped_column(VARCHAR(5), default=None, nullable=True)
    countText: Mapped[str | None] = mapped_column(VARCHAR(5), default=None, nullable=True)
