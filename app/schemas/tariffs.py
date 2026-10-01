from pydantic import BaseModel


class TariffResponse(BaseModel):
    id: str
    month: str
    count: str
    economy: str
    popular: bool
    countTextSum: str
    date: str
    countText: str
