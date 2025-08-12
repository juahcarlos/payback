import base64
import hashlib

from config_be import settings
from cryptography.fernet import Fernet

from libs.logs import log


def init_fernet() -> Fernet:
    """Return a Fernet cipher object for symmetric encryption."""
    key = settings.COOKIE_PASSWORD
    cipher_suite = Fernet(key)
    return cipher_suite


def encrypt_cookie_email(email: str) -> str:
    """Encrypt email address using Fernet cipher object."""
    cipher_suite = init_fernet()
    encoded_text = cipher_suite.encrypt(email.encode("utf-8"))
    return encoded_text.decode("utf-8")


def decrypt_cookie_email(encoded_text: bytes) -> str:
    """Decrypt email address using Fernet cipher object."""
    cipher_suite = init_fernet()
    try:
        decoded_text = cipher_suite.decrypt(encoded_text)
        return decoded_text.decode("utf-8")
    except Exception as ex:
        log.error(f"ERROR: can't decode email from {encoded_text} ex: {ex}")
        

# cryptomus


def sign_cryptomus(data: str) -> str:
    """Create signature for Cryptomus by base64-encoding data and hashing with MD5."""
    data_base64 = base64.b64encode(data.encode("utf-8"))
    sign = hashlib.md5(data_base64 + settings.CRYPT_API_KEY.encode("utf-8")).hexdigest()
    return sign
