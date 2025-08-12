from datetime import datetime, timedelta
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class User(BaseModel):
    email: EmailStr = Field(default=None)
    created: Optional[datetime | str] = datetime.now()
    cn: Optional[str] = ""
    trial: Optional[bool | int | None] = 0
    version_page: Optional[int] = 2
    code: Optional[str] = ""
    coupon: Optional[str] = ""
    expires: Optional[int | str | None] = int(
        (datetime.now() + timedelta(days=30)).strftime("%s")
    )
    plan: Optional[int | None]
    country_iso: Optional[str] = ""
    password: Optional[str] = ""
    reg_source: Optional[str] = ""
    dubious: Optional[bool | int] = 0
    subscribed: Optional[bool | int] = 0
    lang: Optional[str] = ""
    partner_id: Optional[int | None] = 0
    note: Optional[str] = ""


class UserId(User):
    id: int


class UserReminder(UserId):
    unsubscribe_token: Optional[str] = ""


class Coupons(BaseModel):
    coupon: str
    percent: int
    created: Optional[datetime | None] = None
    expiration: datetime
    plans: Optional[str | None] = None


class ReminderArgs(BaseModel):
    try_one_email: Optional[str | None] = None
    no_unsubscribe: Optional[bool] = None


class CustomerPromo(BaseModel):
    address: str
    lang: str


class TransCount(BaseModel):
    count: int
