from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends
from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType
from jinja2 import Environment, FileSystemLoader

from config import email_config, settings
from dbm.database import DbQuery, db
from dbm.schemas import Coupons, CouponsPd, MailData, UserId
from langs.lang import langs
from libs.exceptions import internal_error
from libs.logs import log
from libs.utils import (
    generate_coupon_or_code,
    get_tariffs_monthes,
    get_unsubscribe_token,
)

env = Environment(loader=FileSystemLoader("templates"))


class EmailSender(ABC):
    @abstractmethod
    async def send_mail(self, data: "MailData") -> None:
        """
        Send an email message.
        Args:
            data (MailData): Email content including subject, recipient, and body.
        Raises:
            Exception: On failure to send email.
        """
        ...


class SendMail(EmailSender):
    """
    Email sender class based on FastAPI mail.
    Used via composition by specific email-related classes,
    which create SendMail instances and call its send_mail method.
    """

    def __init__(self, msg_type: MessageType = MessageType.html):
        self.msg_type = msg_type

    async def send_mail(self, data: MailData) -> None:
        """
        Compose and send an email message asynchronously.
        Args:
            data (MailData): Email content including subject, recipient, and body.
        Raises:
            Exception: Raises internal_error if sending fails.
        """
        message = MessageSchema(
            subject=data.subject,
            recipients=[data.email],
            body=data.body,
            subtype=self.msg_type,
        )

        email_conf = ConnectionConfig(**email_config.model_dump())
        fm = FastMail(email_conf)

        fm_send = await fm.send_message(message)
        if fm_send is not None:
            msg = f"send_mail {data.email} send_message errors: {fm_send}"
            log.error(msg)
            raise internal_error(
                "en",
                msg,
            )


class SendCode:
    """
    Class for composing user emails including
    verification codes, coupons, and other content.
    Uses SendMail via composition to send letter.
    """

    def __init__(
        self,
        email_sender: EmailSender,
        db: Annotated[DbQuery, Depends(db)],
        user: UserId,
        tmpl_file: str,
        lang: str = "en",
        amount: int = 0,
    ):
        self.email_sender = email_sender
        self.db = db
        self.user = user
        self.tmpl_file = tmpl_file
        self.lang = lang
        self.amount = amount

    async def mail(self, data) -> str | None:
        """
        Send an email using the SendMail class.
        Args:
            data: MailData object with email content and recipients.
        Returns:
            Optional string result from sending operation.
        """
        return await self.email_sender.send_mail(data)

    async def send(self, subject: str) -> None:
        """
        Compose email body from template and send email with given subject.
        Args:
            subject (str): Email subject.
        """
        body = await self.send_body()

        data = MailData(
            email=self.user.email,
            from_email=settings.FROM_EMAIL,
            subject=subject,
            body=body,
        )

        await self.mail(data)

    async def coupon_add(self) -> CouponsPd:
        """
        Create a new coupon and insert it into the database.
        Returns:
            Coupon instance added to the database.
        """
        coupon = self.coupon_data()
        await self.db.insert_coupon(coupon)
        return coupon

    async def coupon_to_user(self, coupon: str) -> None:
        """
        Assign coupon code to user if they don't have one already.
        Args:
            coupon (str): Coupon code to assign.
        """
        if self.user.coupon is None or self.user.coupon == "":
            await self.db.update_user_coupon(self.user.email, coupon)

    async def send_body(self) -> str | None:
        """
        Render the email body from the template with dynamic data
        including coupon, user plan, and localized texts.
        Returns:
            Rendered email body as a string or None if user is missing.
        """
        coupon = await self.coupon_add()
        await self.coupon_to_user(coupon.coupon)

        if self.user is None:
            return

        if self.user.plan is not None and self.user.plan in [30, 180, 360]:
            tariff = int(self.user.plan / 30)
            tariff_monthes = str(tariff) + " " + get_tariffs_monthes(tariff, self.lang)
        else:
            tariff_monthes = langs(self.lang, "vpn.payment.tariff.monthes.trial")

        template = env.get_template(self.tmpl_file)

        thanks = (
            langs(self.lang, "vpn.payment.done.thanks-trial")
            if self.amount == 0
            else langs(self.lang, "vpn.payment.done.thanks-paid")
        )
        activated = (
            langs(self.lang, "vpn.payment.done.activated-trial")
            if self.amount == 0
            else langs(self.lang, "vpn.payment.done.activated-paid")
        )

        result = template.render(
            email=self.user.email,
            lang=self.lang,
            tariff_monthes=tariff_monthes,
            code=self.user.code,
            coupon=coupon.coupon,
            coupon_percent=coupon.percent,
            setup_plan=activated,
            thanks=thanks,
            install_client=langs(self.lang, "email.access.install-our-client"),
            your_code=langs(self.lang, "email.access.your-code"),
            have_issues=langs(self.lang, "email.access.if-you-have-issues"),
            settings_connection=langs(
                self.lang, "email.access.settings-and-connection"
            ),
            in_attachement=langs(
                self.lang, "email.access.in-attachement-you-find-certs"
            ),
            can_download=langs(self.lang, "email.access.you-can-download-them"),
            read=langs(self.lang, "email.access.read"),
            how_to_set_up=langs(self.lang, "email.access.how-to-configure"),
            how_to_install_on_linux=langs(
                self.lang, "email.access.how-to-install-whoer-vpn-on-linux"
            ),
            addons_mozilla_lang=langs(self.lang, "email.access.addons.mozilla.lang"),
            chrome_lang=langs(self.lang, "email.access.chrome.lang"),
            mail_icons_x=langs(self.lang, "email.access.mail-icons.x"),
            mail_icons_tg=langs(self.lang, "email.access.mail-icons.tg"),
            mail_icons_play_google=langs(
                self.lang, "email.access.mail-icons.play-google"
            ),
            mail_icons_apple_app=langs(self.lang, "email.access.mail-icons.apple-app"),
            unsubscribe_token=get_unsubscribe_token(self.user.email),
            unsubscribe_text=langs(self.lang, "email.access.unsubscribe.text"),
            unsubscribe_tail=langs(self.lang, "email.access.unsubscribe.tail"),
            tullenblick_link=langs(self.lang, "email.access.tullenblick.link"),
            how_to_configure=langs(self.lang, "email.access.how-to-configure"),
            suggestion=langs(self.lang, "email.access.suggestion"),
            suggestion_next=langs(self.lang, "email.access.suggestion.next"),
            your_coupon=langs(self.lang, "email.recovery.your-personal-coupon"),
            coupon_valid=langs(self.lang, "email.recovery.promo-code-valid"),
            # restore
            whoer_hello=langs(self.lang, "email.recovery.whoer-hello"),
            whoer_is_here=langs(self.lang, "email.recovery.whoer-is-here"),
            forgot_your_code=langs(self.lang, "email.recovery.forgot-your-code"),
            here_its_code=langs(self.lang, "email.recovery.here-its-code"),
            thought_discount=langs(self.lang, "email.recovery.whoer-thought-discount"),
            thought_discount_next=langs(
                self.lang, "email.recovery.whoer-thought-discount-next"
            ),
            your_specialist=langs(self.lang, "email.default.your-specialist"),
        )
        return result

    @staticmethod
    def generate_coupon():
        """Generate a new coupon."""
        return generate_coupon_or_code("COUPON")

    def coupon_data(self):
        """
        Create Coupons data class instance with preset discount and expiration
        """
        return Coupons(
            coupon=self.generate_coupon(),
            percent=10,
            created=datetime.now(),
            expiration=datetime.now() + timedelta(days=30),
        )


class EmailSenderFactory:
    @staticmethod
    def create_sender(msg_type: MessageType = MessageType.html) -> EmailSender:
        return SendMail(msg_type=msg_type)


default_email_sender = EmailSenderFactory.create_sender()


async def send_code(
    user: UserId,
    db: Annotated[DbQuery, Depends(db)],
    subject: str,
    tmpl_file: str = "new_user_letter.html",
    amount: int = 0,
) -> None:
    send_code_instance = SendCode(
        db=db,
        user=user,
        tmpl_file=tmpl_file,
        lang=user.lang,
        amount=amount,
        email_sender=default_email_sender,
    )
    await send_code_instance.send(subject)
