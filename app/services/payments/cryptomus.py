import base64
import hashlib
import json
import re
from dataclasses import asdict
from typing import Any

import httpx
from fastapi import Depends

from app.core import exceptions as app_exceptions
from app.core.config import settings
from app.core.logs import log
from app.domain.invoices import CryptomusInvoiceData
from app.domain.payments import PaymentData, PaymentSystem
from app.domain.transactions import TransactionReadModel
from app.schemas import CryptomusConfirmData
from app.services.payments import PaymentService, get_payment_service


class CryptomusService:
    def __init__(self, payment_service: PaymentService) -> None:
        self.payment_service = payment_service

    @staticmethod
    def build_redirect_urls(locale: str) -> tuple[str, str]:
        if locale not in settings.supported_locales:
            locale = settings.default_locale

        frontend_base_url = settings.frontend_base_url.rstrip("/")
        payment_base_url = f"{frontend_base_url}/{locale}/vpn/payment"

        return f"{payment_base_url}/fail", f"{payment_base_url}/success"

    @staticmethod
    def sign_cryptomus(data: str) -> str:
        data_base64 = base64.b64encode(data.encode("utf-8")).decode("utf-8")
        sign = hashlib.md5(  # noqa
            (data_base64 + settings.cryptomus_api_key).encode("utf-8")
        ).hexdigest()
        return sign

    def verify_status(self, status: str | None, data: CryptomusConfirmData) -> bool:
        match status:
            case "confirm_check" | "process" | "wrong_amount_waiting":
                log.info(
                    "CryptomusService verify_status: "
                    "waiting for payment to complete"
                )
                return False

            case "fail" | "system_fail":
                log.error(
                    "CryptomusService verify_status: "
                    "payment has failed (order_id=%s, amount=%s status=%s)",
                    data.order_id, data.amount, status,
                )
                return False

            case "cancel":
                log.warning(
                    "CryptomusService verify_status: "
                    "payment has been canceled (order_id=%s, amount=%s status=%s)",
                    data.order_id, data.amount, status,
                )
                return False

            case "wrong_amount":
                log.warning(
                    "CryptomusService verify_status: "
                    "wrong payment amount",
                )
                return False

            case "paid" | "paid_over":
                log.info(
                    "CryptomusService verify_status: "
                    "got correct status (%s)",
                    status,
                )
                return True

            case _:
                log.warning(
                    "CryptomusService verify_status: "
                    "unhandled status (%s)",
                    status,
                )
                return False

    def check_signature(self, raw_text_data: str, received_signature: str) -> bool:
        body_without_sign = re.sub(r',?"sign"\s*:\s*"[^"]+"', '', raw_text_data)
        body_without_sign = re.sub(r',\s*}', '}', body_without_sign)

        expected_signature = self.sign_cryptomus(body_without_sign)
        if received_signature != expected_signature:
            log.error(
                "CryptomusService check_signature: "
                "wrong signature"
            )
            return False

        return True

    def validate_signature(self, header_signature: str | None, raw_text_data: str) -> None:
        received_sign = header_signature

        if not received_sign:
            try:
                received_sign = json.loads(raw_text_data).get("sign")
            except Exception as exc:  # noqa: BLE001
                log.error(
                    "CryptomusService validate_signature: "
                    "can't load raw body as json (%s)",
                    exc,
                )

        if not received_sign:
            log.error(
                "CryptomusService validate_signature: "
                "no signature in header nor body"
            )
            raise app_exceptions.ClientError()

        if not self.check_signature(raw_text_data, received_sign):
            raise app_exceptions.ClientError()

        return None

    def verify_request(
            self,
            transaction: TransactionReadModel,
            data: CryptomusConfirmData,
    ) -> bool:
        status = data.status

        if not self.verify_status(status=status, data=data):
            return False

        if transaction.complete:
            log.warning(
                "CryptomusService verify_request: "
                "transaction (%s) has been already completed",
                data.order_id,
            )
            return False

        if not transaction.email:
            log.error(
                "CryptomusService verify_request: "
                "transaction has no email"
            )
            return False

        return True

    async def create_request(self, data: dict[str, Any]) -> dict[str, Any]:
        sign = self.sign_cryptomus(
            json.dumps(
                data,
                separators=(",", ":"),
            )
        )

        headers = {
            "merchant": settings.cryptomus_merchant_id,
            "sign": sign,
        }

        async with httpx.AsyncClient(headers=headers) as client:
            try:
                response = await client.post(settings.cryptomus_host, json=data)
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                log.error("CryptomusService: response error (%s)", exc)
                raise app_exceptions.InternalError from exc
            except httpx.RequestError as exc:
                log.error("CryptomusService: request error (%s)", exc)
                raise app_exceptions.InternalError from exc

        resp_data: dict[str, Any] = response.json()

        return resp_data

    async def create_payment(self, data: PaymentData) -> dict[str, Any]:
        trans_data = await self.payment_service.create(data)

        transaction_id = await self.payment_service.trans_repo.insert_transaction(trans_data)

        log.debug(
            "CryptomusService create_payment: transaction for email %s expires = %d",
            trans_data.email,
            int(trans_data.expires.timestamp()),
        )

        url_return, url_success = self.build_redirect_urls(data.lang)

        invoice_data = CryptomusInvoiceData(
            email=data.email,
            amount=str(trans_data.amount),
            currency="USD",
            is_payment_multiple=False,
            lifetime=7200,
            order_id=str(transaction_id),
            url_callback=settings.cryptomus_url_callback,
            url_return=url_return,
            url_success=url_success,
        )

        return await self.create_request(asdict(invoice_data))

    async def confirm_payment(
            self,
            raw_body: bytes,
            header_sign: str | None,
            data: CryptomusConfirmData,
    ) -> None:
        raw_text_data = raw_body.decode()

        self.validate_signature(header_signature=header_sign, raw_text_data=raw_text_data)

        transaction = None

        if data.order_id:
            transaction = await self.payment_service.trans_repo.get_transaction_by_id(int(data.order_id))

        if not transaction:
            log.error(
                "CryptomusService confirm_payment: "
                "transaction %s doesn't exist",
                data.order_id,
            )
            return

        if not self.verify_request(transaction, data):
            return

        log.debug(
            "CryptomusService confirm_payment: transaction for email %s expires = %s",
            transaction.email,
            transaction.expires,
        )

        await self.payment_service.finish_payment(
            payment_id=transaction.id,
            payment_system=PaymentSystem.CRYPTOMUS,
        )

        log.info(
            "CryptomusService confirm_payment: "
            "transaction %s completed",
            data.order_id,
        )

        return


def get_cryptomus_service(
        payment_service: PaymentService = Depends(get_payment_service),  # noqa: B008
) -> CryptomusService:
    return CryptomusService(payment_service=payment_service)
