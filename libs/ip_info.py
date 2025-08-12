from typing import Optional

import geoip2.database
from geoip2.models import City

from config import settings
from libs.logs import log


def geo_data_read() -> geoip2.database.Reader:
    """
    Create and return a GeoIP2 database reader instance.
    Returns:
        geoip2.database.Reader: Reader for GeoIP2 City database.
    """
    reader = geoip2.database.Reader(settings.GEOIP_PATH + "/" + "GeoIP2-City.mmdb")
    return reader


def geo_data(ip: str) -> City:
    """
    Get GeoIP city data for the given IP address.
    Private and local IPs are replaced with
    Google's public DNS IP (8.8.8.8) to ensure lookup.
    Args:
        ip (str): IP address to lookup.
    Returns:
        City | None: GeoIP2 City data if found, otherwise None.
    """
    if (
        ip.startswith("127.")
        or ip.startswith("10.")
        or ip.startswith("172.")
        or ip == "0.0.0.0"
    ):
        ip = "8.8.8.8"

    reader = geo_data_read()
    try:
        geoip_data = reader.city(ip)
        return geoip_data
    except Exception as ex:
        log.error(f"\n\n !!! address {ip} was not found in geoip db ex: {ex}\n\n")


def get_country_iso(ip: str) -> Optional[str]:
    """
    Retrieve the ISO country code for the given IP address.
    Args:
        ip (str): IP address to lookup.
    Returns:
        Optional[str]: Lowercase ISO country code if found, else None.
    """
    geodata = geo_data(ip)
    if geodata:
        iso = geodata.country.iso_code.lower()
        return iso
