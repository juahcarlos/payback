from cryptography.fernet import Fernet

from app.core.config import settings


class CookieService:
    def __init__(self) -> None:
        self.cipher_suite = Fernet(settings.cookie_password)

    def encrypt(self, value: str) -> str:
        encoded_text = self.cipher_suite.encrypt(value.encode("utf-8"))
        return encoded_text.decode("utf-8")

    def decrypt(self, value: str) -> str:
        decoded_text = self.cipher_suite.decrypt(value)
        return decoded_text.decode("utf-8")


def get_cookie_service() -> CookieService:
    return CookieService()
