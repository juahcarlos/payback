import os
import re
import tempfile
import zipfile
from collections.abc import AsyncIterator
from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends

from app.core.config import settings
from app.core.logs import log
from app.domain.certificates import CertificateReadModel, CertificateSaveModel
from app.domain.servers import ServerConfigFileModel
from app.domain.users import UserReadModel
from app.repositories import (
    CertificateDBRepo,
    UserDBRepo,
    get_certificate_repo,
    get_user_repo,
)
from app.services.servers import (
    ServerService,
    ServerType,
    get_server_service,
)
from app.services.translation import (
    TranslationService,
    get_translation_service,
)
from app.utils.certificates import CertificateBuilderService


class EmptyConfigsException(Exception):
    pass


@dataclass(frozen=True)
class ConfigFiles:
    openvpn_zip: str | None
    l2tp_txt: str | None
    sstp_txt: str | None
    softether_txt: str | None


class CertificateService:
    def __init__(
            self,
            certs_repo: CertificateDBRepo,
            user_repo: UserDBRepo,
            server_service: ServerService,
            translation_service: TranslationService,
    ) -> None:
        self.certs_repo = certs_repo
        self.user_repo = user_repo
        self.server_service = server_service
        self.translation_service = translation_service

    @staticmethod
    def get_openvnp_options() -> str:
        with open("app/utils/certificates/openvpn_options.txt", encoding="utf-8") as f:
            options = f.read()

        return options

    async def get_user_certificate(
            self,
            username: str,
    ) -> CertificateSaveModel | CertificateReadModel:
        cert_from_db = await self.certs_repo.get_certificate_by_user_cn(username)
        if cert_from_db:
            return cert_from_db

        cert_dict = CertificateBuilderService().build(username)
        cert_data = CertificateSaveModel(**cert_dict)
        await self.certs_repo.insert_certificate(cert_data)

        return cert_data

    async def get_common_part(self, username: str) -> str:
        certs = await self.get_user_certificate(username)

        config_file = (
            f"{self.get_openvnp_options()}\n\n"
            f"<ca>\n{certs.ca}\n</ca>\n\n"
            f"<cert>\n{certs.cert}</cert>\n\n"
            f"<key>\n{certs.key}</key>\n\n"
            f"<tls-auth>\n{certs.tls}\n</tls-auth>\n"
        )

        config_file = re.sub(r'\\/', '/', config_file)

        return config_file

    async def _assemble_openvpn_certificates(
            self,
            user_data: UserReadModel,
    ) -> list[tuple[str, str, ServerConfigFileModel]]:
        servers_config = await self.server_service.get_active_servers_data(
            server_type="openvpn",
            trial=user_data.email.endswith("@trial.com")
        )

        data = []
        common_part = await self.get_common_part(user_data.cn)
        for iso in servers_config:
            certificate = "".join(
                f"remote {ip} 443 tcp-client\n\n"
                for ip in servers_config[iso].remote_ips
            )
            certificate = f"{certificate}{common_part}"

            data.append((certificate, iso, servers_config[iso]))

        return data

    async def _assemble_l2tp_configs(self, user_data: UserReadModel) -> str | None:
        servers_data = await self.server_service.get_servers_data_for_configs(
            server_type=ServerType.L2TP,
            trial=user_data.email.endswith("@trial.com")
        )

        if not servers_data:
            return None

        configs = []
        configs.append(f"Login: {user_data.cn}, Password: {user_data.password}")

        country_word = self.translation_service.translate_message(
            key="country",
            locale=user_data.lang,
        )
        city_word = self.translation_service.translate_message(
            key="city",
            locale=user_data.lang,
        )
        host_word = self.translation_service.translate_message(
            key="host",
            locale=user_data.lang,
        )

        yes_word = self.translation_service.translate_message(
            key="yes",
            locale=user_data.lang,
        )
        no_word = self.translation_service.translate_message(
            key="no",
            locale=user_data.lang,
        )

        for server_data in servers_data:
            configs.append("")

            country = self.translation_service.translate_message(
                key=f"country.{server_data.iso}",
                locale=user_data.lang,
            )
            city = self.translation_service.translate_message(
                key=f"city.{server_data.city}",
                locale=user_data.lang,
            )

            configs.append(
                "\n".join([
                    f"{country_word}: {country}",
                    f"{city_word}: {city}",
                    f"{host_word}: {server_data.hostname}",
                    f"L2TP Raw: {yes_word if server_data.l2tp_raw else no_word}",
                    f"L2TP/IPsec: {yes_word if server_data.l2tp_ipsec else no_word}",
                    f"IPsec preshared key: {server_data.l2tp_ipsec_preshared_key}",
                ])
            )

        return "\n".join(configs)

    async def _assemble_sstp_configs(self, user_data: UserReadModel) -> str | None:
        servers_data = await self.server_service.get_servers_data_for_configs(
            server_type=ServerType.SSTP,
            trial=user_data.email.endswith("@trial.com")
        )
        if not servers_data:
            return None

        configs = []
        configs.append(f"Login: {user_data.cn}, Password: {user_data.password}")

        country_word = self.translation_service.translate_message(
            key="country",
            locale=user_data.lang,
        )
        city_word = self.translation_service.translate_message(
            key="city",
            locale=user_data.lang,
        )
        host_word = self.translation_service.translate_message(
            key="host",
            locale=user_data.lang,
        )
        port_word = self.translation_service.translate_message(
            key="port",
            locale=user_data.lang,
        )

        for server_data in servers_data:
            configs.append("")

            country = self.translation_service.translate_message(
                key=f"country.{server_data.iso}",
                locale=user_data.lang,
            )
            city = self.translation_service.translate_message(
                key=f"city.{server_data.city}",
                locale=user_data.lang,
            )

            configs.append(
                "\n".join([
                    f"{country_word}: {country}",
                    f"{city_word}: {city}",
                    f"{host_word}: {server_data.hostname}",
                    f"{port_word}: 443",
                ])
            )

        return "\n".join(configs)

    async def _assemble_softether_configs(self, user_data: UserReadModel) -> str | None:
        servers_data = await self.server_service.get_servers_data_for_configs(
            server_type=ServerType.SOFTETHER,
            trial=user_data.email.endswith("@trial.com")
        )
        if not servers_data:
            return None

        configs = []
        configs.append(f"Login: {user_data.cn}, Password: {user_data.password}")

        country_word = self.translation_service.translate_message(
            key="country",
            locale=user_data.lang,
        )
        city_word = self.translation_service.translate_message(
            key="city",
            locale=user_data.lang,
        )
        host_word = self.translation_service.translate_message(
            key="host",
            locale=user_data.lang,
        )
        port_word = self.translation_service.translate_message(
            key="port",
            locale=user_data.lang,
        )

        for server_data in servers_data:
            configs.append("")

            country = self.translation_service.translate_message(
                key=f"country.{server_data.iso}",
                locale=user_data.lang,
            )
            city = self.translation_service.translate_message(
                key=f"city.{server_data.city}",
                locale=user_data.lang,
            )

            configs.append(
                "\n".join([
                    f"{country_word}: {country}",
                    f"{city_word}: {city}",
                    f"{host_word}: {server_data.hostname}",
                    f"{port_word}: 443",
                ])
            )

        return "\n".join(configs)

    @asynccontextmanager
    async def get_openvpn_zip(
            self,
            user_data: UserReadModel,
            zip_name: str = "whoerconfigs_openvpn.zip",
    ) -> AsyncIterator[str]:
        certificates_data = await self._assemble_openvpn_certificates(user_data=user_data)
        if not certificates_data:
            raise EmptyConfigsException()

        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, zip_name)

        try:
            with zipfile.ZipFile(tmp_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for cert, iso, server_data in certificates_data:
                    zip_file.writestr(f"Whoer_{server_data.country_name}_{iso}.ovpn", cert)

            yield tmp_path

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

            if os.path.isdir(tmp_dir):
                os.rmdir(tmp_dir)

    @asynccontextmanager
    async def get_l2tp_txt(
            self,
            user_data: UserReadModel,
            txt_name: str = "whoerconfigs_l2tp.txt",
    ) -> AsyncIterator[str]:
        configs = await self._assemble_l2tp_configs(user_data=user_data)
        if not configs:
            raise EmptyConfigsException()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / txt_name
            path.write_text(configs, encoding="utf-8")
            yield str(path)

    @asynccontextmanager
    async def get_sstp_txt(
            self,
            user_data: UserReadModel,
            txt_name: str = "whoerconfigs_sstp.txt",
    ) -> AsyncIterator[str]:
        configs = await self._assemble_sstp_configs(user_data=user_data)
        if not configs:
            raise EmptyConfigsException()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / txt_name
            path.write_text(configs, encoding="utf-8")
            yield str(path)

    @asynccontextmanager
    async def get_softether_txt(
            self,
            user_data: UserReadModel,
            txt_name: str = "whoerconfigs_softether.txt",
    ) -> AsyncIterator[str]:
        configs = await self._assemble_softether_configs(user_data=user_data)
        if not configs:
            raise EmptyConfigsException()

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / txt_name
            path.write_text(configs, encoding="utf-8")
            yield str(path)

    @asynccontextmanager
    async def get_configs(self, user_id: int) -> AsyncIterator[ConfigFiles]:
        user_data = await self.user_repo.get_user_by_id(user_id=user_id)
        if not user_data:
            raise ValueError(f"CertificatesService get_configs: no user with id = {user_id}")

        async with AsyncExitStack() as stack:
            openvpn = None
            if "openvpn" in settings.configs_to_send:
                try:
                    openvpn = await stack.enter_async_context(self.get_openvpn_zip(user_data))
                except Exception as exc:  # noqa: BLE001
                    log.error(
                        "CertificateService get_configs: couldn't get configs for openvpn (%s)",
                        exc,
                    )

            l2tp = None
            if "l2tp" in settings.configs_to_send:
                try:
                    l2tp = await stack.enter_async_context(self.get_l2tp_txt(user_data))
                except Exception as exc:  # noqa: BLE001
                    log.error(
                        "CertificateService get_configs: couldn't get configs for l2tp (%s)",
                        exc,
                    )

            sstp = None
            if "sstp" in settings.configs_to_send:
                try:
                    sstp = await stack.enter_async_context(self.get_sstp_txt(user_data))
                except Exception as exc:  # noqa: BLE001
                    log.error(
                        "CertificateService get_configs: couldn't get configs for sstp (%s)",
                        exc,
                    )

            softether = None
            if "softether" in settings.configs_to_send:
                try:
                    softether = await stack.enter_async_context(self.get_softether_txt(user_data))
                except Exception as exc:  # noqa: BLE001
                    log.error(
                        "CertificateService get_configs: couldn't get configs for softether (%s)",
                        exc,
                    )

            yield ConfigFiles(
                openvpn_zip=openvpn,
                l2tp_txt=l2tp,
                sstp_txt=sstp,
                softether_txt=softether,
            )


def get_certificate_service(
        certs_repo: CertificateDBRepo = Depends(get_certificate_repo),  # noqa: B008
        user_repo: UserDBRepo = Depends(get_user_repo),  # noqa: B008
        server_service: ServerService = Depends(get_server_service),  # noqa: B008
        translation_service: TranslationService = Depends(get_translation_service),  # noqa: B008
) -> CertificateService:
    return CertificateService(
        certs_repo=certs_repo,
        user_repo=user_repo,
        server_service=server_service,
        translation_service=translation_service,
    )
