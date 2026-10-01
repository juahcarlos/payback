from dataclasses import dataclass
from datetime import datetime

from .base import BaseDomainModel


@dataclass
class BuyFormFillingBaseModel(BaseDomainModel):
    email: str | None = None
    lang: str | None = None


@dataclass
class BuyFormFillingReadModel(BuyFormFillingBaseModel):
    id: int | None = None
    created: datetime | None = None


@dataclass
class BuyFormFillingSaveModel(BuyFormFillingBaseModel):
    email: str | None = None
    lang: str = "en"


@dataclass
class BuyData:
    filling_id: int | None
    filling_token: str | None
    hidden_captcha: str
