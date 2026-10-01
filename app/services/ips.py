from functools import lru_cache

import geoip2.database
from geoip2.errors import AddressNotFoundError
from geoip2.models import City

from app.core.config import settings
from app.core.logs import log
from app.domain.ips import CoordinatesData


class IPInfoService:
    def __init__(self) -> None:
        self.reader = geoip2.database.Reader(
            f"{settings.geoip_path}/GeoIP2-City.mmdb"
        )

    def get_coordinates(self, ip: str) -> CoordinatesData:
        latitude = 22.3539
        longitude = 114.1342

        try:
            geodata = self.reader.city(ip)
        except (AddressNotFoundError, ValueError) as exc:
            log.error("IPInfoService get_coordinates: %s", exc)

        if geodata:
            if geodata.location.latitude:
                latitude = geodata.location.latitude

            if geodata.location.longitude:
                longitude = geodata.location.longitude

        return CoordinatesData(
            latitude=latitude,
            longitude=longitude,
        )

    def get_ip_geo_data(self, ip: str) -> City | None:
        if ip.startswith(("127.", "10.", "172.")) or ip == "0.0.0.0":  # noqa: S104
            ip = "8.8.8.8"

        try:
            geodata = self.reader.city(ip)
            return geodata
        except (AddressNotFoundError, ValueError) as exc:
            log.error("IPInfoService get_ip_geo_data: %s", exc)

        return None

    def get_country_iso(self, ip: str) -> str | None:
        geodata = self.get_ip_geo_data(ip)
        if geodata and geodata.country.iso_code:
            return geodata.country.iso_code.lower()

        return None


@lru_cache
def get_ipinfo_service():
    return IPInfoService()
