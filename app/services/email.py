import hashlib
from dataclasses import fields
from types import MappingProxyType

from fastapi import Depends
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType, NameEmail
from jinja2 import Environment, FileSystemLoader

from app.core import exceptions as app_exceptions
from app.core.config import email_settings, settings
from app.core.logs import log
from app.domain.coupons import CouponSaveModel
from app.domain.emails import EmailSendData
from app.domain.payments import PaymentSystem
from app.domain.users import UserReadModel
from app.repositories import (
    UserDBRepo,
    get_user_repo,
)
from app.services.certificates import (
    CertificateService,
    get_certificate_service,
)
from app.services.coupons import (
    CouponService,
    get_coupon_service,
)
from app.services.translation import (
    TranslationService,
    get_translation_service,
)


env = Environment(
    loader = FileSystemLoader("app/templates"),
    autoescape=True,
)


class EmailSenderService:
    def __init__(
            self,
            data: EmailSendData,
            attachments: list[str] | None = None,
            message_type: MessageType = MessageType.html,
    ) -> None:
        self.data = data
        self.attachments = attachments if attachments else []
        self.message_type = message_type

        connection_config = ConnectionConfig(**email_settings.model_dump())
        self.fast_mail = FastMail(connection_config)

    async def send(self) -> None:  # TODO: retries?
        message = MessageSchema(
            subject=self.data.subject,
            recipients=[NameEmail(name="", email=self.data.email)],
            body=self.data.body,
            subtype=self.message_type,
            attachments=self.attachments,  # type: ignore[arg-type]
            reply_to=[NameEmail(name="", email=settings.email_mail_support)],
        )

        try:
            await self.fast_mail.send_message(message)
        except Exception as exc:
            log.error("EmailSenderService error: %s", exc)
            raise app_exceptions.InternalError() from exc


class EmailService:
    RESTORE_CODE_TEMPLATE = "restore_letter.html"
    NEW_USER_TEMPLATE = "new_user_letter.html"

    MESSAGE_PLAN_MAP = MappingProxyType = MappingProxyType({
        30: "vpn.antidetect.month",
        360: "vpn.antidetect.year",
        720: "vpn.antidetect.years",
    })

    def __init__(
            self,
            user_repo: UserDBRepo,
            coupon_service: CouponService,
            translation_service: TranslationService,
            certificate_service: CertificateService,
    ) -> None:
        self.user_repo = user_repo
        self.coupon_service = coupon_service
        self.translation_service = translation_service
        self.certificate_service = certificate_service

    @staticmethod
    def generate_unsubscribe_token(email: str) -> str:
        value = f"{email}:{settings.email_unsubscribe_secret}"
        return hashlib.sha1(value.encode("utf-8")).hexdigest()  # noqa: S324 TODO: secure

    def _get_tariff_message_key(self, plan: int) -> str:
        return self.MESSAGE_PLAN_MAP.get(plan, "vpn.payment.tariff.months.trial")

    async def _send_email(
            self,
            data: EmailSendData,
            attachments: list[str] | None = None,
    ) -> None:
        email_sender = EmailSenderService(data=data, attachments=attachments)
        await email_sender.send()

    def _assemble_restore_email_body(
            self,
            user_data: UserReadModel,
            coupon_data: CouponSaveModel,
    ) -> str:
        template_filename = self.RESTORE_CODE_TEMPLATE

        template = env.get_template(template_filename)

        template_data_keys = {
            "whoer_hello": "email.recovery.whoer-hello",
            "whoer_is_here": "email.recovery.whoer-is-here",
            "forgot_your_code": "email.recovery.forgot-your-code",
            "here_is_the_code": "email.recovery.here-its-code",
            "thought_discount": "email.recovery.whoer-thought-discount",
            "thought_discount_next": "email.recovery.whoer-thought-discount-next",
            "coupon_valid": "email.recovery.promo-code-valid",
            "your_specialist": "email.default.your-specialist",
            "mail_icons_play_google": "email.access.mail-icons.play-google",
            "mail_icons_apple_app": "email.access.mail-icons.apple-app",
            "unsubscribe_text": "email.access.unsubscribe.text",
            "unsubscribe_tail": "email.access.unsubscribe.tail",
        }

        transalations = {}
        for template_key, message_key in template_data_keys.items():
            transalations[template_key] = self.translation_service.translate_message(
                key=message_key,
                locale=user_data.lang,
            )

        result = template.render(
            code=user_data.code,
            coupon_percent=coupon_data.percent,
            coupon=coupon_data.coupon,
            lang=user_data.lang or "en",
            email=user_data.email,
            unsubscribe_token=self.generate_unsubscribe_token(user_data.email),
            **transalations,
        )

        return result

    async def _assemble_new_user_email_body(
            self,
            user_data: UserReadModel,
            coupon_data: CouponSaveModel | None,
            template_file: str,
    ) -> str:
        template = env.get_template(template_file)

        template_data_keys = {
            "thanks": "vpn.payment.done.thanks-paid",
            "setup_plan": "vpn.payment.done.activated-paid",
            "your_code": "email.access.your-code",
            "install_client": "email.access.install-our-client",
            "how_to_install_on_linux": "email.access.how-to-install-whoer-vpn-on-linux",
            "mail_icons_play_google": "email.access.mail-icons.play-google",
            "mail_icons_apple_app": "email.access.mail-icons.apple-app",
            "manage_subscription_text": "email.access.autorenewal.info",
            "manage_subscription_link_text": "email.access.autorenewal.link",
            "in_attachement": "email.access.in-attachement-you-find-certs",
            "can_download": "email.access.you-can-download-them",
            "tullenblick_link": "email.access.tullenblick.link",
            "read": "email.access.read",
            "how_to_set_up": "email.access.how-to-configure",
            "unsubscribe_text": "email.access.unsubscribe.text",
            "unsubscribe_tail": "email.access.unsubscribe.tail",
            "suggestion": "email.access.suggestion",
            "suggestion_next": "email.access.suggestion.next",
            "coupon_valid": "email.recovery.promo-code-valid",
        }

        transalations = {}
        for template_key, message_key in template_data_keys.items():
            transalations[template_key] = self.translation_service.translate_message(
                key=message_key,
                locale=user_data.lang,
            )

        result = template.render(
            code=user_data.code,
            manage_subscription_link=None,
            coupon_percent=coupon_data.percent if coupon_data else None,
            coupon=coupon_data.coupon if coupon_data else None,
            lang=user_data.lang or "en",
            email=user_data.email,
            unsubscribe_token=self.generate_unsubscribe_token(user_data.email),
            **transalations,
        )

        return result

    async def send_restore_email(self, user_data: UserReadModel) -> None:
        coupon_data = await self.coupon_service.create_new_coupon()

        if not user_data.coupon:
            await self.user_repo.update_user_coupon(
                user_data.email,
                coupon_data.coupon,
            )

        email_body = self._assemble_restore_email_body(user_data, coupon_data)

        subject = self.translation_service.translate_message(
            "email.recovery.subject",
            locale=user_data.lang,
        )

        email_data = EmailSendData(
            email=user_data.email,
            from_email=settings.email_whoer_email,
            subject=subject,
            body=email_body,
        )

        try:
            async with self.certificate_service.get_configs(user_id=user_data.id) as config_files:
                attachments = [
                    getattr(config_files, field.name)
                    for field in fields(config_files)
                    if getattr(config_files, field.name) is not None
                ]
                await self._send_email(
                    data=email_data,
                    attachments=attachments,
                )
        except Exception as exc:  # noqa: BLE001
            log.error("EmailService send_restore_email: error (%s)", exc)
            return

        log.info("EmailService send_restore_email: email sent (%s)", user_data.email)

    async def send_new_user_email(
            self,
            user_data: UserReadModel,
            payment_system: PaymentSystem,
    ) -> None:
        template_file = self.NEW_USER_TEMPLATE

        coupon_data = await self.coupon_service.create_new_coupon()

        if not user_data.coupon:
            await self.user_repo.update_user_coupon(
                user_data.email,
                coupon_data.coupon,
            )

        email_body = await self._assemble_new_user_email_body(
            user_data=user_data,
            coupon_data=coupon_data,
            template_file=template_file,
        )

        subject = self.translation_service.translate_message(
            "email.access.subject",
            locale=user_data.lang,
        )

        email_data = EmailSendData(
            email=user_data.email,
            from_email=settings.email_whoer_email,
            subject=subject,
            body=email_body,
        )

        try:
            async with self.certificate_service.get_configs(user_id=user_data.id) as config_files:
                attachments = [
                    getattr(config_files, field.name)
                    for field in fields(config_files)
                    if getattr(config_files, field.name) is not None
                ]
                await self._send_email(
                    data=email_data,
                    attachments=attachments,
                )
        except Exception as exc:  # noqa: BLE001
            log.error("EmailService send_new_user_email: error (%s)", exc)
            return

        log.info("EmailService send_new_user_email: email sent (%s)", user_data.email)


def get_email_service(
        user_repo: UserDBRepo = Depends(get_user_repo),  # noqa: B008
        coupon_service: CouponService = Depends(get_coupon_service),  # noqa: B008
        translation_service: TranslationService = Depends(get_translation_service),  # noqa: B008
        certificate_service: CertificateService = Depends(get_certificate_service),  # noqa: B008
) -> EmailService:
    return EmailService(
        user_repo=user_repo,
        coupon_service=coupon_service,
        translation_service=translation_service,
        certificate_service=certificate_service,
    )
