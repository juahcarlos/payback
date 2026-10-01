from pydantic import BaseModel


class FillingQueryParams(BaseModel):
    id: int
    token: str
    email: str
    lang: str = "en"


class FillingResponse(BaseModel):
    encrypted_email: str
