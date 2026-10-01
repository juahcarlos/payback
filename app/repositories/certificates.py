from dataclasses import asdict

from sqlalchemy import delete, insert, select

from app.domain.certificates import (
    CertificateReadModel,
    CertificateSaveModel,
)
from app.models import Certs

from .base import BaseDBRepo


class CertificateDBRepo(BaseDBRepo):

    # CREATE

    async def insert_certificate(self, cert_data: CertificateSaveModel) -> None:
        statement = insert(Certs).values(**asdict(cert_data))
        await self.insert_only(statement)

    # READ

    async def get_certificate_by_user_cn(self, user_cn: str) -> CertificateReadModel | None:
        statement = select(Certs).filter_by(username=user_cn)
        return await self.select_one(statement, CertificateReadModel)

    # DELETE

    async def delete_certificate_by_user_cn(self, user_cn: str) -> None:
        statement = delete(Certs).where(Certs.username == user_cn)
        await self.delete(statement)


def get_certificate_repo() -> CertificateDBRepo:
    return CertificateDBRepo()
