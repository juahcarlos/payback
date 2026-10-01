# ruff: noqa: F401

from .admins import AdminAuthDBRepo, get_admin_auth_repo
from .buy_form_filling import BuyFormFillingDBRepo, get_buy_form_filling_repo
from .certificates import CertificateDBRepo, get_certificate_repo
from .coupons import CouponDBRepo, get_coupon_repo
from .partners import PartnerDBRepo, get_partner_repo
from .servers import ServerDBRepo, get_server_repo
from .tariffs import TariffDBRepo, get_tariff_repo
from .transactions import TransactionDBRepo, get_transaction_repo
from .users import UserDBRepo, get_user_repo
