from dataclasses import dataclass

from .base import BaseDomainModel


@dataclass
class CertificateBaseModel(BaseDomainModel):
    ca: str
    cert: str
    key: str
    tls: str
    username: str | None = None


@dataclass
class CertificateReadModel(CertificateBaseModel):
    pass


@dataclass
class CertificateSaveModel(CertificateBaseModel):
    pass
