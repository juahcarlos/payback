"""
This module has 2 blocks of functions
The first named "render_*" generates HTML code for customer letters
mostly related to purchased services.
These letters may include access codes, discount coupons, service
usage instructions, software download links, and other related information.

The second named "send_*" compiles the letters using the template renderer
mentioned above and send them to users from the given lists.
"""

from datetime import datetime
from typing import List

from config import settings
from crontabs.db.db_query import dbq
from libs.utils import generate_coupon_db, render_tmpl
from crontabs.lib.utils import langs
from dbm.schemas import UserId, MailData
from libs.send_mail import default_email_sender as EmailSender


class BaseRender:
    """Abstract base class for all email renderers."""

    async def render(self, user: UserId) -> str:
        raise NotImplementedError


class RemindRender(BaseRender):
    """Render reminder email."""

    async def render(self, user: UserId) -> str:
        lang = user.lang
        email = user.email
        data_tmpl = {
            "header_notice_expired": langs[
                f"email.reminder-new.header-notice-expired-{lang}"
            ],
            "email_reminder_new_herd": langs[f"email.reminder-new.herd-{lang}"],
            "email_reminder_new_herd_discount": langs[
                f"email.reminder-new.herd-discount-{lang}"
            ],
            "email_reminder_new_promocode": langs[
                f"email.reminder-new.promocode-{lang}"
            ],
            "email_reminder_new_promocode_valid": langs[
                f"email.reminder-new.promocode-valid-{lang}"
            ],
            "email_reminder_new_use_safety": langs[
                f"email.reminder-new.use-safety-{lang}"
            ],
            "email_reminder_new_buy_vpn": langs[f"email.reminder.buy-vpn-{lang}"],
            "email_reminder_new_support": langs[f"email.reminder-new.support-{lang}"],
            "email_reminder_new_support_chat": langs[
                f"email.reminder-new.support-chat-{lang}"
            ],
            "email_reminder_new_support_email": langs[
                f"email.reminder-new.support-email-{lang}"
            ],
            "email_reminder_new_unsubscribe": langs[
                f"email.reminder-new.unsubscribe-{lang}"
            ],
            "email_reminder_new_unsubscribe_here": langs[
                f"email.reminder-new.unsubscribe-here-{lang}"
            ],
            "email.reminder_new_sincerely": langs[
                f"email.reminder-new.sincerely-{lang}"
            ],
            "link_lang": lang + "/" if lang != "en" else "",
            "email": email,
            "unsubscribe_token": settings.UNSUBSCRIBE_SECRET,
            "localtime": datetime.now().strftime("%Y"),
        }

        now_unix = int(datetime.now().timestamp())
        if now_unix - user.expires > 0:
            coupon = await generate_coupon_db(dbq, 10, 30)
            data_tmpl["coupon"] = coupon.coupon

        return render_tmpl("template/reminder_new.html", data_tmpl)


class PromoRender(BaseRender):
    """Render new customer promo email."""

    async def render(self, user: UserId) -> str:
        coupon = await generate_coupon_db(dbq, 35, 1, "180,360")
        return render_tmpl(
            f"template/email/newcustomer_promo_{user.lang}.html",
            {"coupon": coupon.coupon, "localtime": datetime.now().strftime("%Y")},
        )


class CouponRender(BaseRender):
    """Render new customer coupon email."""

    async def render(self, user: UserId) -> str:
        coupon = await generate_coupon_db(dbq, 25, 1, "180,360")
        return render_tmpl(
            f"template/email/newcustomer_coupon_{user.lang}.html",
            {"coupon": coupon.coupon, "localtime": datetime.now().strftime("%Y")},
        )


class MailService:
    """Service for sending emails using registered renderers."""

    def __init__(self, sender: EmailSender):
        self.sender = sender
        self.renderers = {
            cls.__name__.lower(): cls() for cls in BaseRender.__subclasses__()
        }

    async def send_all(self, renderer_name: str, users: List[UserId], subject: str):
        renderer = self._get_renderer(renderer_name)
        for user in users:
            body = await renderer.render(user)
            subj = langs[f"{subject}-{user.lang}"]
            await self.sender.send_mail(
                MailData(email=user.email, subject=subj, body=body)
            )

    async def send_one(self, renderer_name: str, user: UserId, subject: str):
        renderer = self._get_renderer(renderer_name)
        body = await renderer.render(user)
        subj = langs[f"{subject}-{user.lang}"]
        await self.sender.send_mail(MailData(email=user.email, subject=subj, body=body))

    def _get_renderer(self, name: str) -> BaseRender:
        try:
            return self.renderers[name.lower()]
        except KeyError:
            raise ValueError(f"Renderer not found: {name}")


_sender = EmailSender
_mail_service = MailService(_sender)


async def send_all_reminder(users: List[UserId]) -> list | None:
    return await _mail_service.send_all(
        "remindrender", users, "email.subjects.reminder"
    )


async def send_new_customer_promos(users: List[UserId]) -> list | None:
    return await _mail_service.send_all(
        "promorender", users, "email.subjects.newcustomer_promo"
    )


async def send_new_customer_coupons(users: List[UserId]) -> list | None:
    return await _mail_service.send_all(
        "couponrender", users, "email.subjects.newcustomer_coupon"
    )
