from pydantic import BaseModel


class CryptomusCreateResponse(BaseModel):
    pass


class CryptomusCreateQueryParams(BaseModel):
    email: str
    plan: str
    hidden_captcha: str
    coupon: str | None = None
    permanent: bool = False
    lang: str = "en"


class CryptomusConvert(BaseModel):
    to_currency: str | None = None
    commission: str | None = None
    rate: str | None = None
    amount: str | None = None


class CryptomusConfirmData(BaseModel):
    type: str | None = None
    uuid: str | None = None
    order_id: str | None = None
    amount: str | None = None
    payment_amount: str | None = None
    payment_amount_usd: str | None = None
    merchant_amount: str | None = None
    commission: str | None = None
    is_final: bool = False
    status: str | None = None
    from_: str | None = None
    wallet_address_uuid: str | None = None
    network: str | None = None
    currency: str | None = None
    payer_currency: str | None = None
    additional_data: str | None = None
    convert: CryptomusConvert | None = None
    txid: str | None = None
    sign: str | None = None


class PaymentFailedResponse(BaseModel):
    message: str


class PaymentSuccessResponse(BaseModel):
    message: str
    code: str = ""
    email: str = ""
    country_iso: str = ""
    url_redirect: str = ""


class CheckoutSessionResponse(BaseModel):
    id: str
    url: str | None = None
