import hashlib
import random
import string
from datetime import datetime, timedelta

import geoip2.database
from fastapi.templating import Jinja2Templates
from jinja2 import Template

from config import settings
from dbm.schemas import CouponsPd
from langs.lang import langs
from libs.logs import log

templates = Jinja2Templates(directory="templates")


def generate_code():
    """Return "KEY" + 10 random uppercase letters or digits"""
    return generate_coupon_or_code("KEY")


async def code_for_user(db):
    """Call code generator and check if no user in DB with the same code"""
    code = generate_code()
    log.debug(f"utils.code_for_user code {code}")
    code_in_db = await db.get_user_by_code(code)
    if code_in_db is not None:
        return await code_for_user(db)
    return code


def generate_password():
    """Generate password using random letters and digits"""
    return "".join(
        [random.choice(string.ascii_letters + string.digits) for _ in range(12)]
    ).lower()


async def generate_coupon_db(db, cents, expiration, plans=None):
    """Call coupon generator and insert it in DB"""
    coupon_data = generate_coupon_or_code()
    data = CouponsPd(
        coupon=coupon_data,
        percent=cents,
        created=datetime.now(),
        expiration=datetime.now() + timedelta(days=expiration),
        plans=plans,
    )

    await db.insert_coupon(data)
    return data


def get_tariffs_monthes(tariff, lang="en"):
    """Just set the dict with numbers of months and names of related tariff"""
    tariffs_monthes = {
        1: langs(lang, "vpn.antidetect.mounth"),
        6: langs(lang, "vpn.antidetect.mounths"),
        12: langs(lang, "vpn.antidetect.year"),
    }
    return tariffs_monthes[tariff]


def generate_coupon_or_code(what=""):
    """Universal generator of random letters and digits with given part"""
    return (
        what
        + "".join(
            [random.choice(string.ascii_letters + string.digits) for _ in range(10)]
        ).upper()
    )


def get_unsubscribe_token(email):
    """Generate code that will be asked if user will want to unsubscribe"""
    token = hashlib.sha1(
        (email + ":" + settings.UNSUBSCRIBE_SECRET).encode("utf-8")
    ).hexdigest()
    return token


def geo_data(ip):
    if ip == "127.0.0.1" or ip == "0.0.0.0" or ip == "" or ip is None:
        ip = "45.9.46.142"
    with geoip2.database.Reader(
        settings.GEOIP_PATH + "/" + "GeoIP2-City.mmdb"
    ) as reader:
        try:
            geoip_data = reader.city(ip)
            return geoip_data
        except Exception as ex:
            log.error(f"\n\n !!! address {ip} was not found in geoip db ex: {ex} \n\n")


def get_country_iso(ip):
    geodata = geo_data(ip)
    if geodata:
        iso = geodata.country.iso_code.lower()
        return iso


def render_tmpl(tmpl_file, data):
    log.info(f"\n\n tmpl_file {tmpl_file}\n\n")
    with open(tmpl_file) as f:
        template = Template(f.read())
        output = template.render(data)
        return output
