from datetime import datetime

from sqlalchemy import (
    TIMESTAMP,
    VARCHAR,
    BigInteger,
    Boolean,
    Column,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.types import DECIMAL

Base = declarative_base()


class Coupons(Base):
    """
    Coupon model representing discount coupons with usage limits, expiration,
    and applicability to subscription plans.
    """

    __tablename__ = "coupons"

    coupon = Column(String(250), default="", nullable=False, primary_key=True)
    max_use_limit = Column(Integer)
    percent = Column(Integer)
    prolong = Column(Integer)
    times_used = Column(Integer)
    manual = Column(Boolean, default=False, nullable=True)
    expiration = Column(
        TIMESTAMP,
        default=datetime.strptime("2038-01-19 03:14:07", "%Y-%m-%d %H:%M:%S"),
        nullable=True,
    )
    description = Column(Text, default=None, nullable=True)
    created = Column(
        TIMESTAMP,
        default=datetime.now(),
        nullable=True,
    )
    plans = Column(String(64), default=None, nullable=True)

    __table_args__ = (
        Index("coupons_coupon", "coupon", unique=True),
        Index("manual_created", "manual", "created"),
    )


class Transactions(Base):
    """
    Transaction model recording payment details, status, related user email,
    applied coupons, and partner information.
    """

    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True)
    system = Column(String(100), default=None, nullable=True)
    data = Column(Text)
    days = Column(Integer)
    amount = Column(DECIMAL(10, 2))
    email = Column(VARCHAR(250), default="", nullable=True)
    expires = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    created = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    trial = Column(Boolean, default=True, nullable=True)
    coupon = Column(String(250), default=None, nullable=True)
    version_page = Column(Integer)
    country_iso = Column(String(2), default="-", nullable=True)
    complete = Column(Boolean, default=False, nullable=True)
    partner_amount = Column(DECIMAL(10, 2))
    partner_id = Column(BigInteger, default=0, nullable=True)
    partner_referrer_id = Column(BigInteger, default=0, nullable=True)
    pushed_by = Column(String(250), default=None, nullable=True)
    remote_amount = Column(DECIMAL(10, 2))
    check_order_id = Column(BigInteger, default=0, nullable=True)
    pay_time = Column(Integer)
    remote_status = Column(VARCHAR(255), default=None, nullable=True)
    credited = Column(String(255), default=None, nullable=True)
    json_custom_fields = Column(String(8000))
    remote_invoice_id = Column(String(8000))
    refund = Column(Boolean, default=0, nullable=True)

    __table_args__ = (
        Index("transactions_email", "email"),
        Index("transactions_email_complete", "email", "complete"),
        Index("transactions_trial", "trial"),
        Index("transactions_created", "created"),
        Index("transactions_expires", "expires"),
        Index("transactions_partner_id", "partner_id"),
        Index("transactions_coupon", "coupon", "created"),
        Index("transactions_complete_created", "complete", "created"),
    )


class Users(Base):
    """
    User model storing account information, authentication data, subscription
    status, and related metadata.
    """

    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True)
    email = Column(VARCHAR(150), default="", nullable=False)
    created = Column(TIMESTAMP, default=datetime.now(), nullable=False)
    cn = Column(String(100), default=None, nullable=True)
    trial = Column(Boolean, default=False, nullable=True)
    version_page = Column(Integer, default=0, nullable=True)
    code = Column(String(250), default=None, nullable=True)
    coupon = Column(String(250), default=None, nullable=True)
    expires = Column(Integer, default=None, nullable=True)
    plan = Column(Integer, default=None, nullable=True)
    country_iso = Column(String(2), default="-", nullable=True)
    password = Column(String(100), default="", nullable=True)
    reg_source = Column(String(100), default="web", nullable=True)
    dubious = Column(Boolean, default=False, nullable=False)
    subscribed = Column(Boolean, default=False, nullable=False)
    lang = Column(String(2), default="en", nullable=False)
    partner_id = Column(BigInteger, default=None, nullable=True)
    note = Column(Text, default=None, nullable=True)

    __table_args__ = (
        Index("id", "id", unique=True),
        Index("users_code_expires", "code", "expires"),
        Index("users_trial", "trial"),
        Index("users_dubious", "dubious"),
        Index("users_expires", "expires", mysql_using="BTREE"),
        Index("users_created", "created"),
        Index("trial_expires", "trial", "expires"),
    )
