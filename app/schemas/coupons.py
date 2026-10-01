from pydantic import BaseModel


class CouponCheckQueryParams(BaseModel):
    coupon: str
    tariff: str | None = None


class CouponCheckResponse(BaseModel):
    percent: int
    prolong: int
