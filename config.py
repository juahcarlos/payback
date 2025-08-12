from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Base settings shared across multiple services in this monorepo.
    """

    PROD: int = 0
    # --- database
    PREFIX: str = "mysql+aiomysql"
    LOGIN: str = "root"
    PASSWORD: str = "88ddbblala"
    HOST: str = "127.0.0.1"
    PORT: str = "3306"
    DATABASE: str = "mobile"
    GRPC_HOST: str = "localost"
    GRPC_PORT: int = 9091

    # --- redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS: str = "redis://localhost/0"

    PROMETEUS_LOGIN: bytes = b"stanleyjobson"
    PROMETEUS_PASSWORD: bytes = b"swordfisha"
    USE_EXCLUDED_ENDPOINTS: bool = False

    # --- mail
    NEW_USER_SUBJECT: str = "Whoer VPN код авторизации"
    FROM_EMAIL: str = "adtgastbr@gmail.com"
    SEND_ERROR: str = """Sending operations has failed.
        We will try to solve the problem you as soon as possible.
        """
    BASE_URL: str = "http://localhost:8081"
    FRONTEND_BASE_URL: str = "https://localhost"

    # --- test
    TEST_EMAIL: str = "srntsfrtnshjs@gmail.com"
    TEST_CODE: str = "KEYIDUEHFNRTY"
    TEST_PLAN: int = 30
    TEST_TOKEN: str = "6dd8255a1ed581340e3b2e02165cfc5e0f0f1e1b"
    TEST_LANG: str = "ru"

    GEOIP_PATH: str = "geoip"

    # --- scripts
    UNSUBSCRIBE_SECRET: str = "RSwrNfsOm7zGzhAoFxb3"

    LANGS: list = [
        "en",
        "ru",
        "fr",
        "cz",
        "de",
        "es",
        "it",
        "jp",
        "nl",
        "pl",
        "pt",
        "tr",
        "zh",
    ]

    PLANS: str = """{
      "payment_systems": [
        "freekassa",
        "freekassa2",
        "appstore",
        "lava",
        "playmarket",
        "enot",
        "paypal",
        "cryptonator",
        "twocheckout",
        "cryptomus",
        "stripe"
      ],
      "plans": {
        "180": {
          "appstore": "whoerVPN.6_months_subscription",
          "link": "https://localhost/en/vpn?action=buy&plan=180",
          "order": 1,
          "period": {
            "name": "months",
            "num": "6",
            "type": "access"
          },
          "playmarket": "com.whoer.vpn_test_180",
          "price": "39.0$",
          "save": "35%",
          "special": "1"
        },
        "30": {
          "appstore": "whoerVPN.1_month_subscription",
          "link": "https://localhost/en/vpn?action=buy&plan=30",
          "order": 0,
          "period": {
            "name": "month",
            "num": "1",
            "type": "access"
          },
          "playmarket": "com.whoer.vpn_test_30",
          "price": "9.9$",
          "save": "0%",
          "special": "0"
        },
        "360": {
          "appstore": "whoerVPN.1_year_subscription",
          "link": "https://localhost/en/vpn?action=buy&plan=360",
          "order": 2,
          "period": {
            "name": "year",
            "num": "1",
            "type": "access"
          },
          "playmarket": "com.whoer.vpn_test_360",
          "price": "46.9$",
          "save": "60%",
          "special": "0"
        }
      },
      "status": "OK"
}"""


settings = Settings()


# email
class EmailConfig(BaseSettings):
    MAIL_USERNAME: str = "aml"
    MAIL_PASSWORD: str = "CheckAml856"
    MAIL_FROM: str = "vpn@whoer.net"
    MAIL_FROM_NAME: str = "Mr.Whoer"
    MAIL_PORT: int = 10025
    MAIL_SERVER: str = "mail.whoer.net"
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    USE_CREDENTIALS: bool = True
    VALIDATE_CERTS: bool = False


email_config = EmailConfig()
