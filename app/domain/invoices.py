from dataclasses import dataclass
from datetime import datetime


@dataclass
class CryptomusInvoiceData:
    email: str
    amount: str
    currency: str
    order_id: str = ""
    is_payment_multiple: bool = False
    lifetime: int = 7200
    url_callback: str = "confirmation"
    url_return: str = "return"
    url_success: str = "success"
    to_currency: str = ""
    time_client: datetime | None = None
