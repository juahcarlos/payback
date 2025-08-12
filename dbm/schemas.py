from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class CouponsPd(BaseModel):
    """
    Coupon data with validation of 'expiration' field
    """

    coupon: str
    max_use_limit: Optional[int] = 0
    percent: int
    prolong: Optional[int] = 0
    times_used: Optional[int] = 0
    manual: Optional[int | None] = None
    created: Optional[datetime | str] = datetime.now()
    expiration: Optional[datetime | str] = "2038-01-19 03:14:07"
    plans: Optional[str | None] = None

    @field_validator("expiration", mode="before")
    def fix_zeros(cls, value):
        if value == "0000-00-00 00:00:00":
            value = "2038-01-01 00:00:00"
        if isinstance(value, datetime):
            return value
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


class Coupons(BaseModel):
    """
    Coupon data with selected set of fields
    """

    coupon: str
    percent: int
    created: datetime
    expiration: datetime


class TransactionFull(BaseModel):
    """
    Full transaction data including unique identifier (ID)
    """

    id: Optional[int | str] = None
    system: Optional[str] = None
    data: Optional[str] = "{}"
    days: Optional[int] = None
    amount: Optional[float] = None
    email: EmailStr | None = Field(default=None)
    created: Optional[datetime] = None
    expires: Optional[datetime] = None
    trial: Optional[bool] = None
    coupon: Optional[str] = None
    version_page: Optional[int] = None
    country_iso: Optional[str] = None
    complete: Optional[bool] = None
    partner_id: Optional[int] = None
    partner_amount: Optional[float] = None
    partner_referrer_id: Optional[int] = None
    pushed_by: Optional[str] = None
    remote_amount: Optional[float] = None
    check_order_id: Optional[int] = None
    pay_time: Optional[int] = None
    remote_status: Optional[str] = None
    credited: Optional[str] = None
    json_custom_fields: Optional[str] = None
    remote_invoice_id: Optional[str] = None
    refund: Optional[bool] = None
    status: Optional[str] = "OK"


class User(BaseModel):
    """
    Basic user account data for registration and initial database insertion.
    """

    email: EmailStr | None = Field(default=None)
    created: Optional[datetime] = datetime.now()
    expires: Optional[int | str | None] = int(
        (datetime.now() + timedelta(days=30)).strftime("%s")
    )
    code: Optional[str] = ""
    country_iso: Optional[str] = "us"
    password: Optional[str] = ""
    reg_source: Optional[str] = "web"
    plan: Optional[int] = 0
    lang: Optional[str] = "en"
    trial: Optional[bool | int | None] = 0
    version_page: Optional[int] = 0


class UserFull(User):
    """
    Extended user info including flag for mailings,
    cn (inner username) for login to purchased resources,
    coupon, partner info, and notes.
    """

    cn: Optional[str] = ""
    coupon: Optional[str] = ""
    dubious: Optional[int] = 0
    subscribed: Optional[int] = 1
    partner_id: Optional[int | None] = None
    note: Optional[str] = ""
    status: Optional[str] = "OK"


class UserId(UserFull):
    """Extends UserFull with id field"""

    id: int | None = Field(default=None)


class UserInsertEmail(UserFull):
    """Extends UserFull with has_user field"""

    has_user: Optional[bool] = False


class MailSource(BaseModel):
    """Provides 2 fields for use in Payment class"""

    email: str | None = Field(default=None)
    source: Optional[str] = "web"


class MailData(BaseModel):
    """Email data to send letters"""

    name: Optional[str] = None
    from_email: Optional[str] = None
    email: str
    subject: str
    body: str
