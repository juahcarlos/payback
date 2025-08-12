import time
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dbm.schemas import MailSource
from typing import Annotated, Optional

from redis.asyncio.client import Redis
from config_be import settings
from dbm.redis_db import rdb
from db.schemas import PaymentContext, TransactionFull, TransactionSave
from dbm.schemas import UserId
from fastapi import Depends
from langs.lang import langs
from lib.domain.buy.utils import decrypt_cookie_email

from be.db.database import DbQuery, db
from be.lib.domain.buy.payment_check import CheckMixin
from libs.exceptions import error_404
from libs.logs import  log
from libs.send_mail import SendCode
from libs.users import insert_mail
from libs.utils import (
    generate_coupon_db,
    generate_coupon_or_code,
    get_country_iso,
)


class Payment(ABC, CheckMixin):
    """
    Base class for API handlers for payment processing with Freekassa payment system
    """
    async def create(self, ctx: PaymentContext) -> PaymentContext:
        """
        Prepare and initiate the payment process by validating the payment context,
        Create a new transaction (self.trans) and store it as an instance attribute
        for use in subclass-specific payment processing, delegating payment creation to derived
        classes, which should extend this method to complete payment processing.

        Performs checks on IP rate limits, email, coupon, and blacklist.
        Applies coupon to the price, calculates final amount.
        Creates or updates user record in database.

        Args:
            ctx: Freekassa payment data (PaymentContext).
        Returns:
            PaymentContext: When all validation and processing succeed.
            str: "fail" if the IP rate limit is exceeded.
        """
        if await self._check_ip_in_time(ctx) == 0:
            return "fail"

        ctx = self._fix_email(ctx)
        print(f"************  Payment after _fix_email ctx {ctx}")
        ctx = await self._check_of_fix_plan(ctx)
        print(f"************  Payment after _check_of_fix_plan ctx {ctx}")
        
        await self._check_coupon(ctx)
        await self._check_already_sent(ctx)
        await self._is_blacklisted_email_hosting(ctx)

        country_code = get_country_iso(ctx.ip)
        amount = await self.calc_amount_with_coupon(ctx)

        user = await insert_mail(
            data=MailSource(email=ctx.email),
            db=self.db,
            ip=ctx.ip,
            lang=ctx.lang,
            subject=langs(ctx.lang, "email.subjects.access"),
            amount=amount,
        )
        trans_data = await self.set_trans_data(user, ctx, amount, country_code)
        self.trans = await self.transaction(trans_data)
        return ctx

    async def set_trans_data(self, user, ctx, amount, country_code):
        """
        Prepare transaction data structure with user, payment context, amount,
        and country information.

        Args:
            user: User object from the database.
            ctx: PaymentContext containing payment request data.
            amount: Calculated payment amount.
            country_code: ISO code of the user's country.

        Returns:
            TransactionSave: Prepared transaction data ready for insertion.
        """
        trans_data = TransactionSave(
            system=ctx.currency,
            days=ctx.plan,
            amount=amount,
            email=ctx.email,
            created=datetime.now(),
            expires=datetime.now() + timedelta(days=3),
            trial=True if amount == 0 else False,
            coupon=ctx.coupon,
            country_iso=country_code,
            complete=False,
            partner_id=user.partner_id,
            refund=0,
        )
        trans_data = await self.calc_partner_amount(user, trans_data)
        return trans_data

    async def transaction(self, trans_data: TransactionFull) -> TransactionFull:
        """
        Insert transaction data into the database and return the created record.

        Args:
            trans_data: TransactionSave data to insert.

        Returns:
            TransactionFull: Inserted transaction record with generated fields.
        """
        trans = await self.db.insert_transaction(trans_data)
        return trans

    @abstractmethod
    async def confirmation(self):
        """
        Handle payment system webhook:
        1. Validate the incoming data.
        2. If valid — update transactions.complete from 0 to 1.
        3. Return the expected response to the payment system.
        """

    async def success(self, email_cookie: str = None) -> str:
        """
        Return success message after payment completion.

        Decrypts email from the cookie to identify user,
        fetches user data, and prepares a localized response.

        Args:
            email_cookie (str, optional): Encrypted user email cookie.

        Returns:
            dict: Success message with optional redirect URL and user info,
                  or error message if cookie is missing.
        """
        if email_cookie is None:
            message = {
                "message": "Cookie are switching off or session has been terminated",
                "code": "",
            }
            return message
        email = decrypt_cookie_email(email_cookie)
        message = await self.compile_message(email, email_cookie)
        return message

    async def fail(self, email_cookie: str = None) -> str:
        """
        Compile and return a localized payment failure message for the user.

        Args:
            email_cookie (str, optional): Encrypted email aquired from cookie
            on frontend used to get the user
            from database to determine its language.

        Returns:
            dict: A dict containing the localized failure message.
                If `email_cookie` is not provided or invalid, use English.
        """
        lang = "en"
        if email_cookie:
            email = decrypt_cookie_email(email_cookie)
            if email:
                user = await self.db.get_user_by_email(email)
                lang = user.lang

            msg = (
                f'{langs(lang, "vpn.payment.fail.header")}\n\n'
                f'{langs(lang, "vpn.payment.fail.message")}'
            )
        else:
            msg = f"You need to enable cooke in you browser to use our services"

        message = {"message": msg}
        return message

    async def compile_message(self, email: str, email_cookie: str) -> str:
        """
        Generate a message and optional redirect URL,
        get user by email, pick language and country,
        create a message and redirect URL if needed,
        and return a dictionary with the result.

        Args:
            email: User email.
            email_cookie: Encrypted email cookie for URL redirect.

        Returns:
            dict: Result dictionary with keys:
                - 'message': message string,
                - 'url_redirect' (optional): redirect URL,
                - 'email': user email,
                - 'code': user code,
                - 'country_iso' (optional): user country code.
            If user not found, returns dict with:
                - 'message': error message,
                - 'code': empty string,
                - 'email': empty string.
        """
        message = {}
        if email:
            user = await self.db.get_user_by_email(email)
            if user is None:
                raise error_404("en")

            lang = user.lang
            if user.country_iso == "ru" and user.lang != "ru":
                lang = "ru"
                url_redirect = (
                    f"{settings.FRONTEND_BASE_URL}/{lang}"
                    f"/vpn/payment/success?email_cookie={email_cookie}"
                )
                message["url_redirect"] = url_redirect

            if user.trial is True or user.trial == 1:
                msg = langs(lang, "vpn.payment.done.thanks-trial") + "\n\n"
                msg += langs(lang, "vpn.payment.done.activated-trial")
            else:
                msg = langs(lang, "vpn.payment.done.thanks-paid") + "\n\n"
                msg += langs(lang, "vpn.payment.done.activated-paid") + "\n\n"
                msg += langs(lang, "vpn.payment.done.activated-paid-info")

            message["message"] = msg
            message["email"] = user.email
            message["code"] = user.code

            if user.country_iso == "ru" and lang != "ru":
                message["country_iso"] = user.country_iso
        else:
            message = {
                "message": f"User was not found by email {email}",
                "code": "",
                "email": "",
            }
        return message

    async def calc_partner_amount(self, user, trans_data: TransactionFull) -> str:
        """
        Calculate partner's commission and update transaction data.

        Args:
            user: User object containing partner info.
            trans_data: Transaction data to update.

        Returns:
            TransactionFull: Updated transaction data with partner amount.
        """
        if user.partner_id is not None:
            partner = await self.db.get_partner(user.partner_id)
            trans_data.partner_amount = round(
                trans_data.amount * partner.commission / 100, 2
            )
        return trans_data

    async def calc_amount_with_coupon(self, ctx: PaymentContext) -> int | None:
        """
        Calculate the amount after applying a coupon discount.

        Args:
            ctx: PaymentContext containing payment request data.

        Returns:
            float: Discounted amount rounded to 2 decimals.
        """
        coupon_db = await self.db.get_coupon(ctx.coupon)
        plan_db = await self.db.get_tariff(ctx.plan)

        print(f"************  Payment calc_amount_with_coupon ctx {ctx}")

        amount = float(plan_db.countTextSum)

        if coupon_db is not None:
            amount *= (100 - coupon_db.percent) / 100
        return round(amount, 2)

    async def apply_trans_data_to_user(self, trans: TransactionFull) -> UserId:
        """
        Update user record based on the given transaction data.

        This includes setting coupon, extending expiration,
        adjusting trial status, and saving changes to the database.

        Args:
            trans: Transaction data to apply.

        Returns:
            Updated user record in the database.
        """
        user = await self.db.get_user_by_email(trans.email)

        if user.code is None:
            user.code = generate_coupon_or_code("KEY")

        if user.coupon is None:
            coupon = await generate_coupon_db(
                self.db,
                10,
                30,
            )
            user.coupon = coupon.coupon

        elapsed_time = 0
        now_unix = int(time.time())
        if user.expires > now_unix and user.trial == 0:
            elapsed_time = user.expires - now_unix
        user.expires = now_unix + trans.days * 86400 + elapsed_time

        # add coupon with prolongation
        trans_coupon = await self.db.get_coupon(trans.coupon)
        if trans_coupon is not None and trans_coupon.prolong > 0:
            user.expires += int(trans.days * 86400 * trans_coupon.prolong / 100)

        user.trial = user.trial and trans.trial
        user.plan = trans.days

        await self.db.update_user_full_finish(user)
        user_res = await self.db.get_user_by_email(user.email)
        return user_res

    async def full_finish_payment_by_id(self, payment_id) -> None:
        """
        Complete payment process by payment ID.

        Marks the transaction as complete, updates coupon usage,
        applies transaction data to the user record, and updates
        transaction expiration date. Also triggers sending notification email.

        Args:
            payment_id: ID of the payment transaction to finalize.

        Returns:
            None
        """
        trans = await self.db.get_trans_by_id(payment_id)
        await self.db.update_trans_complete(payment_id)
        await self.db.update_coupon_times_used(trans.coupon)
        user = await self.apply_trans_data_to_user(trans)
        trans_expires = datetime.fromtimestamp(user.expires)
        await self.db.update_trans_expires(trans_expires, payment_id)
        await send_code(user, self.db, langs(user.lang, "email.subjects.access"))


class PaymentAll(Payment):
    """
    Create a minimally initialized object to serve fail or success endpoints.
    """
    def __init__(
        self,
        db: Annotated[DbQuery, Depends(db)],
        rdb: Optional[Annotated[Redis, Depends(rdb)]] = None,
    ):
        self.db = db
        self.rdb = rdb

    async def confirmation(self):
        pass
