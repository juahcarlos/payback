from dataclasses import dataclass

from .base import BaseDomainModel


@dataclass
class AdminAuthReadData(BaseDomainModel):
    username: str
    password: str
