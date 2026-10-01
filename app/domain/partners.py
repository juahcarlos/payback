from dataclasses import dataclass
from datetime import datetime

from .base import BaseDomainModel


@dataclass
class PartnerReadModel(BaseDomainModel):
    id: int
    created: datetime
    password: str
    commission: int
    description: str
    lang: str
