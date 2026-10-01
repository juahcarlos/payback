# ruff: noqa: F401

from .admins import AdminService, get_admin_service
from .buy import BuyService, get_buy_service
from .certificates import CertificateService, get_certificate_service
from .code import CodeService, get_code_service
from .cookie import CookieService, get_cookie_service
from .coupons import CouponService, get_coupon_service
from .email import EmailService, get_email_service
from .ips import IPInfoService, get_ipinfo_service
from .servers import (
    ServerService,
    ServerUpdateService,
    get_server_service,
    get_server_update_service,
)
from .tariffs import TariffService, get_tariff_service
from .translation import TranslationService, get_translation_service
from .users import UserService, get_user_service
