import hashlib

from app.core.config import settings
from app.services.buy import BuyService


def get_service() -> BuyService:
    return BuyService(repo=None, locale="en")  # type: ignore[arg-type]


def test_hidden_captcha_is_valid_from_another_ip() -> None:
    service = get_service()
    captcha = service.get_hidden_captcha("192.0.2.1")

    assert service.check_hidden_captcha("198.51.100.2", captcha)


def test_hidden_captcha_rejects_tampering() -> None:
    service = get_service()
    captcha = service.get_hidden_captcha("192.0.2.1")

    assert not service.check_hidden_captcha("192.0.2.1", f"{captcha}tampered")


def test_hidden_captcha_rejects_expired_token(monkeypatch) -> None:
    service = get_service()
    monkeypatch.setattr("app.services.buy.time.time", lambda: 1_000)
    captcha = service.get_hidden_captcha("192.0.2.1")
    monkeypatch.setattr(
        "app.services.buy.time.time",
        lambda: 1_000 + service.HIDDEN_CAPTCHA_TTL_SECONDS + 1,
    )

    assert not service.check_hidden_captcha("192.0.2.1", captcha)


def test_hidden_captcha_accepts_legacy_token_for_rolling_deploy() -> None:
    service = get_service()
    ip = "192.0.2.1"
    legacy_captcha = hashlib.sha256(
        f"{ip}{settings.hidden_captcha_secret}".encode()
    ).hexdigest()

    assert service.check_hidden_captcha(ip, legacy_captcha)
    assert not service.check_hidden_captcha("198.51.100.2", legacy_captcha)
