import hashlib
import hmac

from app.core.config import settings


def get_sign_hash(value: bytes) -> str:
    return hmac.new(
        settings.signature_secret.encode(),
        value,
        digestmod=hashlib.sha256,
    ).hexdigest()
