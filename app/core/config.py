import json

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    # Admin auth

    auth_max_failed_attempts: int = 5
    auth_window_seconds: int = 60

    # Env

    prod: int = 0
    stage: int = 0

    # Application

    allowed_origins: str | list[str] = ["https://whox.is", "https://whovpn.net", "https://whoxtelega.xyz"]
    supported_locales: list[str] = [
        "cz", "de", "en", "es", "fr", "it","jp",
        "nl", "pl", "pt", "ru", "tr", "zh",
    ]
    locale_param_name: str = "lang"
    default_locale: str = "en"
    cookie_password: str
    be_host: str = "http://139.59.133.127:8093"
    frontend_base_url: str = "https://whovpn.net"
    buy_filling_secret: str
    hidden_captcha_secret: str
    reg_sources: list[str] = ["android", "ios", "proxy", "web"]
    protocols: list[str] = ["openvpn", "ikev2", "proxies", "sstp", "softether", "l2tp"]
    base_url: str = "http://localhost:8081"
    admin_be: str = "http://localhost:8082"
    legacy_app_url: str = "https://martha.whoer.net"
    static_url: str = 'https://whox.is/static'
    email_unsubscribe_secret: str
    email_whoer_email: str = "donrodrigess@gmail.com"
    email_mail_support: str = "who@whoer.net"
    email_send_error: str = """Sending operations have failed.
        We will try to solve the problem as soon as possible.

        """
    email_code_is_none_message: str = "User doesn't have a code, needs to buy a VPN tariff"
    email_recovery_interval_seconds: int = 60

    # Geoip

    geoip_path: str = "geoip"
    geoip_file: str = "GeoIP2-City.mmdb"
    geoip_country: str = "GeoIP2-Country.mmdb"
    geoisp_file: str = "GeoIP2-ISP.mmdb"
    tor_file: str = "udger3_strangehosts.mmdb"
    fennec_brandhost: str = "fennec_brandhosts.mmdb"
    tor_base: str = "https://check.torproject.org/exit-addresses"

    # Configs

    zip_files_path: str = "temp/zip"
    configs_to_send: list[str] = ["openvpn"]

    # Servers

    stat_interval: int = 60000000
    server_secret_key: str
    server_domain: str = "sechwhapi.net"

    # Database

    database_url: str

    # Redis

    redis_url: str = "redis://localhost/0"
    redis_startup_check: bool = True

    # Payments

    tariffs_promo_active: bool = False
    signature_secret: str

    ## Cryptomus

    cryptomus_merchant_id: str = ""
    cryptomus_api_key: str = ""
    cryptomus_secret_key: str
    cryptomus_host: str = "https://api.cryptomus.com/v1/payment"
    cryptomus_allowed_hosts: list[str] = [
        "139.59.133.127",
        "193.108.118.249",
        "91.227.144.54",
        "localhost",
        "0.0.0.0",  # noqa: S104
        "127.0.0.1",
    ]
    cryptomus_url_callback: str = "http://139.59.133.127:8093/vpn/payment/confirmation/cryptomus"
    cryptomus_test_mode: bool = True

    # Prometheus

    prometheus_enabled: bool = False
    prometheus_login: bytes
    prometheus_password: bytes
    use_excluded_endpoints: bool = False

    # Test

    test_email: str = "test@gmail.com"
    test_email_support: str = "testsupp@gmail.com"
    test_access_code: str = "KEYMNKH5WAGKW"
    test_tariff_plan: int = 30
    test_token: str = "cca82fe2ba9fa02043eaa362ddd6054af67ba0b8"  # noqa: S105
    test_lang: str = "ru"
    trial_username: str = "cn0"
    trial_password: str = "aezeephohp"  # noqa: S105

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: list[str] | str) -> list[str]:
        if isinstance(v, list):
            return v

        if isinstance(v, str):
            v = v.strip()

            if v.startswith("["):
                try:
                    data: list[str] = json.loads(v)
                    return data
                except (json.JSONDecodeError, TypeError) as exc:
                    raise ValueError("Wrong ALLOWED_ORIGINS value") from exc

            if "," in v:
                return [origin.strip() for origin in v.split(",")]

            return [v]

        return []


settings = Settings()


class FastAPIMailConfig(BaseSettings):
    MAIL_USERNAME: str = "aml"
    MAIL_PASSWORD: str
    MAIL_FROM: str = "from@mymaildomain.net"
    MAIL_FROM_NAME: str = "Mr.Me"
    MAIL_PORT: int = 10025
    MAIL_SERVER: str = "mail.mymaildomain.net"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = False


email_settings = FastAPIMailConfig()
