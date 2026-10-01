from dataclasses import dataclass
from enum import StrEnum


class PaymentSystem(StrEnum):
    CRYPTOMUS = "cryptomus"
    HELEKET = "heleket"


@dataclass
class PaymentData:
    email: str
    plan: str
    system: PaymentSystem
    hidden_captcha: str
    ip: str = "127.0.0.1"
    lang: str = "en"
    coupon: str | None = None
    permanent: bool = False


@dataclass
class PaymentSuccess:
    message: str = ""
    code: str = ""
    email: str = ""
    country_iso: str = ""
    url_redirect: str = ""
