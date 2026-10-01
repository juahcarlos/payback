from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from app.utils.datetime import utc_now_naive
from app.utils.email import normalize_email

from .base import BaseDomainModel


@dataclass
class UserBaseModel(BaseDomainModel):
    email: str
    plan: int = 0
    code: str = ""
    expires: int = field(default_factory=lambda: int((datetime.now(UTC) + timedelta(days=30)).timestamp()))
    trial: bool = False

    def __post_init__(self) -> None:
        self.email = normalize_email(self.email)


@dataclass
class UserPaymentInputData:
    email: str
    country_iso: str
    amount: float
    source: str = "web"
    trial: bool = False

    def __post_init__(self) -> None:
        self.email = normalize_email(self.email)


@dataclass
class UserCreateModel(UserBaseModel):
    created: datetime = field(default_factory=utc_now_naive)
    country_iso: str = "us"
    password: str = ""
    reg_source: str = "web"
    lang: str = "en"
    version_page: int = 0


@dataclass(kw_only=True)
class UserReadModel(UserCreateModel):
    id: int
    cn: str = ""
    coupon: str = ""
    dubious: int = 0
    subscribed: int = 1
    partner_id: int | None = None
    note: str = ""
    status: str = "OK"


@dataclass
class UserUpdateModel(UserBaseModel):
    coupon: str = ""


@dataclass
class UserDataModel:
    user_id: int
    expires: int
    plan: int
    subscribed: bool


@dataclass
class UserCountModel(BaseDomainModel):
    active: int
