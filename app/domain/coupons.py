from dataclasses import dataclass, field
from datetime import UTC, datetime

from app.utils.datetime import utc_now_naive

from .base import BaseDomainModel


@dataclass
class CouponBaseModel(BaseDomainModel):
    coupon: str
    percent: int
    created: datetime | str = field(
        default_factory=utc_now_naive
    )
    expiration: datetime = field(  # type: ignore[call-overload]
        default_factory=lambda: datetime(2038, 1, 1, tzinfo=UTC)
    )


@dataclass(kw_only=True)
class CouponReadModel(CouponBaseModel):
    prolong: int
    max_use_limit: int | None = None
    times_used: int | None = None
    manual: int | None = None
    plans: str | None = None
    description: str | None = None

    def __post_init__(self):
        # Fix expiration value
        if not isinstance(self.expiration, datetime):
            if self.expiration == "0000-00-00 00:00:00":
                self.expiration = "2038-01-01 00:00:00"

            self.expiration = datetime.strptime(
                self.expiration,
                "%Y-%m-%d %H:%M:%S"
            ).replace(tzinfo=UTC)


@dataclass
class CouponSaveModel(CouponBaseModel):
    pass


@dataclass
class CouponCheckModel(BaseDomainModel):
    percent: int
    prolong: int
