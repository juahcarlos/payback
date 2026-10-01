from dataclasses import dataclass

from .base import BaseDomainModel


@dataclass
class TariffBaseModel(BaseDomainModel):
    month: str
    count: str
    economy: str
    popular: bool
    countTextSum: str  # TODO: correct case
    date: str
    countText: str


@dataclass
class TariffReadModel(TariffBaseModel):
    id: str
