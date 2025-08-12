from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from libs.logs import log

# be


class Coupon(BaseModel):
    """
    Coupon information with discount, validity, and usage limits.

    Note:
        'Expiration' date validator replaces zero-date string
        with the default "end of times" date (2038-01-01).
    """
    coupon: str
    percent: int
    prolong: int
    created: datetime
    expiration: datetime
    times_used: int | None = Field(default=None)
    max_use_limit: int | None = Field(default=None)

    @field_validator("expiration", mode="before")
    def fix_zeros(cls, value):
        log.debug(f"db.schemas value {value}")
        if value == "0000-00-00 00:00:00":
            value = "2038-01-01 00:00:00"
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")


class CouponCheck(BaseModel):
    """Minimal coupon data for validation."""
    percent: int
    prolong: int


class FormCreate(BaseModel):
    """User input form data for starting a purchase."""
    email: str
    plan: int
    permanent: bool
    coupon: Optional[str] = None
    currency: str


class FreekassaConfirmData(BaseModel):
    """Webhook data from Freekassa."""
    intid: Optional[str | int] = None
    MERCHANT_ORDER_ID: Optional[str | int] = None
    SIGN: Optional[str] = None
    MERCHANT_ID: Optional[str] = None
    AMOUNT: Optional[str | float | int] = None
    P_EMAIL: Optional[str] = None
    P_PHONE: Optional[str | int] = None
    CUR_ID: Optional[str | int] = None
    payer_account: Optional[str | int] = None
    commission: Optional[str | float | int] = None
    ip: Optional[str] = None
    lang: Optional[str] = None


class InvoiceData(BaseModel):
    """Parameters for invoice creation."""
    email: Optional[str] = ""
    amount: Optional[int | str | float] = None
    currency: Optional[str] = ""
    order_id: Optional[str] = ""
    is_payment_multiple: Optional[bool] = False
    lifetime: Optional[int] = 7200
    url_callback: Optional[str] = "confirmation"
    url_return: Optional[str] = "return"
    url_success: Optional[str] = "success"
    to_currency: Optional[str] = ""
    time_client: Optional[datetime] = None  # datetime.now()


class Count(BaseModel):
    """
    Wraps count from the database into a data class
    to unify format and DB data flow.
    """
    count: int | None = Field(default=None)


class TransactionSave(BaseModel):
    """Transaction data for inserting into the DB."""
    system: str | None = Field(default="")
    data: str = "{}"
    days: int
    amount: float
    email: EmailStr | None = Field(default=None)
    created: Optional[datetime] = datetime.now()
    expires: Optional[datetime] = datetime.now() + timedelta(hours=2)
    trial: Optional[bool] = False
    coupon: Optional[str] = ""
    version_page: Optional[int] = 2
    country_iso: Optional[str] = "us"
    complete: Optional[bool] = False
    partner_id: Optional[int] = 0
    partner_amount: Optional[float] = 0
    partner_referrer_id: Optional[int] = 0
    check_order_id: Optional[int] = 0
    refund: Optional[bool] = False


class TransactionFull(BaseModel):
    """Returned transaction data from DB select queries."""
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


class Coupons(BaseModel):
    """List of coupons."""
    coupon: str
    percent: int
    created: datetime
    expiration: datetime


class TariffsWhPd(BaseModel):
    """Special tariff data formatted for frontend."""
    id: str
    month: str
    count: str
    economy: str
    popular: bool
    countTextSum: str
    date: str
    countText: str


class PaymentContext(BaseModel):
    """Payment data flow operations."""
    email: str
    coupon: Optional[str] = None
    plan: int = 0
    lang: Optional[str] = "en"
    ip: str = "127.0.0.1"
    currency: str = "free"
    permanent: Optional[str] = None
    trial: bool = False


class PaymentContextTrial(BaseModel):
    """Payment data flow operations for trial users."""
    email: str
    ip: str
    lang: str
    currency: str


class Partner(BaseModel):
    id: int
    created: datetime
    password: str
    commission: int
    description: str
    lang: str


class Mail(BaseModel):
    """Wrapped to PD formatter email address"""
    email: EmailStr | None = Field(default=None)

