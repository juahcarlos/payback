from pydantic import BaseModel


class BuyResponse(BaseModel):
    filling_id: int
    filling_token: str
    hidden_captcha: str
