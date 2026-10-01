from datetime import datetime
from pathlib import Path

import pytest

from app.core import exceptions as app_exceptions
from app.domain.coupons import CouponSaveModel
from app.domain.payments import PaymentSystem
from app.domain.users import UserReadModel
from app.services.code import CodeService
from app.services.email import EmailService
from app.services.translation import TranslationService


LOCALES_PATH = Path(__file__).parents[2] / "app" / "locales"
NOW = datetime(2026, 1, 1)


def get_user(lang: str = "ru", email: str = "some+user@test.com") -> UserReadModel:
    return UserReadModel(id=1, email=email, code="KEYTEST", lang=lang, created=NOW)


def get_coupon() -> CouponSaveModel:
    return CouponSaveModel(coupon="COUPONTEST", percent=10, created=NOW, expiration=NOW)


class FakeRedis:
    def __init__(self) -> None:
        self.keys: set[str] = set()

    async def eval(self, _script: str, numkeys: int, *args: str | int) -> int:
        keys = [str(key) for key in args[:numkeys]]
        if any(key in self.keys for key in keys):
            return 0
        self.keys.update(keys)
        return 1


class FakeUserRepo:
    def __init__(self, user: UserReadModel) -> None:
        self.user = user

    async def get_user_by_email(self, email: str) -> UserReadModel:
        return self.user

    async def update_user_coupon(self, email: str, coupon: str) -> None:
        pass


class FakeCouponService:
    def __init__(self) -> None:
        self.created = 0

    async def create_new_coupon(self) -> CouponSaveModel:
        self.created += 1
        return get_coupon()


class FakeEmailService:
    def __init__(self) -> None:
        self.sent = 0

    async def send_restore_email(self, user_data: UserReadModel) -> None:
        self.sent += 1


class FakeCertificateService:
    def get_configs(self, user_id: int) -> None:
        raise RuntimeError("no configs in tests")


def get_email_service(coupon_service: FakeCouponService | None = None) -> EmailService:
    return EmailService(
        user_repo=FakeUserRepo(get_user()),  # type: ignore[arg-type]
        coupon_service=coupon_service or FakeCouponService(),  # type: ignore[arg-type]
        translation_service=TranslationService(LOCALES_PATH),
        certificate_service=FakeCertificateService(),  # type: ignore[arg-type]
    )


def test_translation_falls_back_to_en_for_missing_locale() -> None:
    service = TranslationService(LOCALES_PATH)
    en_subject = service.translate_message("email.access.subject", "en")

    assert service.translate_message("email.access.subject", None) == en_subject
    assert service.translate_message("email.access.subject", "xx") == en_subject


def test_restore_email_body_has_translations_and_unsubscribe_link() -> None:
    service = get_email_service()
    coupon = get_coupon()

    ru_body = service._assemble_restore_email_body(get_user("ru"), coupon)
    en_body = service._assemble_restore_email_body(get_user("en"), coupon)

    assert "UNKNOWN" not in ru_body
    assert "Держите, не благодарите" in ru_body
    assert "https://whoer.net/ru/unsubscribe?email=some%2Buser%40test.com&token=" in ru_body
    assert "https://whoer.net/unsubscribe?email=some%2Buser%40test.com&token=" in en_body


@pytest.mark.parametrize("payment_system", [PaymentSystem.CRYPTOMUS])
async def test_new_user_email_body(payment_system: PaymentSystem) -> None:
    service = get_email_service()
    template = service.NEW_USER_TEMPLATE
    coupon = get_coupon()

    body = await service._assemble_new_user_email_body(get_user("de"), coupon, template)

    assert "UNKNOWN" not in body
    assert "whox.is" not in body
    assert "https://whoer.net/unsubscribe?email=" in body


async def test_recovery_email_is_rate_limited_per_email() -> None:
    email_service = FakeEmailService()
    service = CodeService(
        user_repo=FakeUserRepo(get_user(email="User@Test.com")),  # type: ignore[arg-type]
        email_service=email_service,  # type: ignore[arg-type]
        redis=FakeRedis(),  # type: ignore[arg-type]
    )

    await service.restore_access_code("User@Test.com", "192.0.2.1")

    with pytest.raises(app_exceptions.ErrorRecoveryRateLimited):
        await service.restore_access_code("User@Test.com", "192.0.2.1")

    assert email_service.sent == 1
