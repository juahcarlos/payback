from dataclasses import dataclass, field
from datetime import datetime, timedelta

from app.utils.datetime import utc_now_naive

from .base import BaseDomainModel


@dataclass
class TransactionBaseModel(BaseDomainModel):
    days: int
    amount: float
    email: str
    system: str = ""
    created: datetime = field(
        default_factory=utc_now_naive
    )
    expires: datetime = field(
        default_factory=lambda: utc_now_naive() + timedelta(hours=2)
    )
    trial: bool = False
    coupon: str | None = None
    version_page: int = 2
    country_iso: str = "us"
    complete: bool = False
    partner_id: int | None = None
    partner_amount: float | None = None
    partner_referrer_id: int | None = None
    check_order_id: int = 0
    refund: bool = False

    def __post_init__(self):
        if isinstance(self.amount, str):
            self.amount = float(self.amount)


@dataclass
class TransactionSaveModel(TransactionBaseModel):
    pass


@dataclass(kw_only=True)
class TransactionReadModel(TransactionBaseModel):
    id: int
    data: str = "{}"
    pushed_by: str | None = None
    remote_amount: float | None = None
    pay_time: int | None = None
    remote_status: str | None = None
    credited: str | None = None
    json_custom_fields: str | None = None
    remote_invoice_id: str | None = None
    status: str = "OK"


@dataclass
class TransactionsCountModel(BaseDomainModel):
    count: int | None = None
