import hashlib
import hmac
import secrets
import time

from fastapi import Depends

from app.core.config import settings
from app.core.locale import get_current_locale
from app.domain.buy_form_filling import BuyData, BuyFormFillingSaveModel
from app.repositories.buy_form_filling import (
    BuyFormFillingDBRepo,
    get_buy_form_filling_repo,
)


class BuyService:
    HIDDEN_CAPTCHA_TTL_SECONDS = 60 * 60
    HIDDEN_CAPTCHA_CLOCK_SKEW_SECONDS = 60

    def __init__(self, repo: BuyFormFillingDBRepo, locale: str) -> None:
        self.repo = repo
        self.locale = locale

    @staticmethod
    def get_buy_filling_token(filling_id: int) -> str:
        value = f"{filling_id}:{settings.buy_filling_secret}"
        hash_value = hashlib.sha256(value.encode("utf-8"))
        return hash_value.hexdigest()

    @staticmethod
    def get_hidden_captcha(ip: str) -> str:
        del ip  # The token must survive legitimate client IP changes.
        issued_at = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        payload = f"{issued_at}.{nonce}"
        signature = hmac.new(
            settings.hidden_captcha_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return f"{payload}.{signature}"

    def check_hidden_captcha(self, ip: str, hidden_captcha: str) -> bool:
        try:
            issued_at_raw, nonce, signature = hidden_captcha.split(".", maxsplit=2)
            issued_at = int(issued_at_raw)
        except (AttributeError, TypeError, ValueError):
            # Keep already opened purchase pages working during a rolling deploy.
            legacy_value = f"{ip}{settings.hidden_captcha_secret}"
            legacy_captcha = hashlib.sha256(legacy_value.encode("utf-8")).hexdigest()
            return hmac.compare_digest(hidden_captcha, legacy_captcha)

        now = int(time.time())
        if issued_at > now + self.HIDDEN_CAPTCHA_CLOCK_SKEW_SECONDS:
            return False
        if now - issued_at > self.HIDDEN_CAPTCHA_TTL_SECONDS:
            return False

        payload = f"{issued_at_raw}.{nonce}"
        expected_signature = hmac.new(
            settings.hidden_captcha_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        if hmac.compare_digest(signature, expected_signature):
            return True
        return False

    async def get_buy_data(self, ip: str = "127.0.0.1") -> BuyData:
        data = BuyFormFillingSaveModel(email=None, lang=self.locale)

        hidden_captcha = self.get_hidden_captcha(ip)

        filling_id: int | None = None
        if (filling := await self.repo.insert_filling(data)):
            filling_id = filling.id

        if not filling_id:
            return BuyData(
                filling_id=None,
                filling_token=None,
                hidden_captcha=hidden_captcha,
            )

        token = self.get_buy_filling_token(filling_id)

        return BuyData(
            filling_id=filling_id,
            filling_token=token,
            hidden_captcha=hidden_captcha,
        )

    async def check_filling(self, filling_id: int, token: str) -> bool:
        if not await self.repo.get_filling_by_id(filling_id):
            return False

        if token != self.get_buy_filling_token(filling_id):
            return False

        return True

    async def update_filling(self, filling_id: int, email: str) -> None:
        await self.repo.update_filling(filling_id, email)


def get_buy_service(
        repo: BuyFormFillingDBRepo = Depends(get_buy_form_filling_repo),  # noqa: B008
        locale: str = Depends(get_current_locale),
) -> BuyService:
    return BuyService(repo, locale)
