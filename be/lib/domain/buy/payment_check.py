import re

from config_be import settings
from lib.domain.buy.buy import check_coupon
from lib.exceptions import already_sent, blacklisted_email

from be.db.schemas import PaymentContext, PaymentContextTrial
from libs.exceptions import internal_error
from libs.logs import log


class CheckMixin:
    async def _check_already_sent(self, ctx: PaymentContext) -> None:
        """
        Checks if a trial email has already been sent recently using Redis cache.
        Args:
            ctx (PaymentContext): Payment details.
        Raises:
            already_sent: If Redis key "<email>:trial" exists.
        """
        if ctx.currency == "free":
            rkey_trial = ctx.email + ":trial"
            cached = await self.rdb.get(rkey_trial)
            if cached:
                raise already_sent(ctx.lang)
            await self.rdb.setex(rkey_trial, 60, 1)

    async def _check_of_fix_plan(self, ctx: PaymentContext) -> None:
        """
        Sets default plan to free or validates plan selection.
        Args:
            ctx (PaymentContext): Payment context.
        Raises:
            internal_error: If plan not selected for paid currency.
        Returns:
            PaymentContext: Possibly updated Payment context.
        """
        if ctx.plan is None and ctx.currency == "free":
            ctx.plan = 0
        if not ctx.plan and ctx.currency != "free":
            raise internal_error(ctx.lang, "You need to choose tariff plan")
        return ctx

    async def _check_coupon(self, ctx: PaymentContext) -> None:
        """
        Validates the coupon code.
        Args:
            ctx (PaymentContext): Payment details.
        Raises:
            internal_error: If coupon is invalid.
        """
        check = await check_coupon(self.db, ctx.coupon)
        if check == 0:
            raise internal_error(ctx.lang, "Wrong coupon")

    async def _check_ip_in_time(self, ctx: PaymentContext) -> int | None:
        """
        Limits number of requests per IP for free or PayPal currencies.
        Args:
            ctx (PaymentContext): Payment details.
        Returns:
            int | None: 0 if limit exceeded, else None.
        """
        if ctx.currency in ["free", "paypal"]:
            rediskey = "ip_count_" + ctx.currency + ":" + ctx.ip
            ip_amount = int(await self.rdb.get(rediskey) or 0)
            log.debug(f"_check_ip_in_time ip_amount {ip_amount}")
            if ip_amount >= 2:
                return 0
            ip_amount += 1
            await self.rdb.setex(rediskey, 60, ip_amount)

    async def _is_blacklisted_email_hosting(self, ctx: PaymentContext) -> None:
        """
        Checks if email domain is blacklisted.
        Args:
            ctx (PaymentContext): Payment details.
        Raises:
            blacklisted_email: If domain has found in the black list in Redis.
        """
        email_domain = re.sub(r"^.*?@", "", ctx.email)
        if await self.rdb.exists("blacklist:email:" + email_domain):
            raise blacklisted_email(ctx.lang)

    def _fix_email(
            self, ctx: PaymentContext | PaymentContextTrial
    ) -> PaymentContext | PaymentContextTrial:
        """
        Fixes email domain based on known corrections.
        Args:
            ctx (PaymentContext | PaymentContextTrial): Payment details.
        Returns:
            PaymentContext | PaymentContextTrial: Possibly updated PaymentContextTrial.
        """
        email_domain = re.sub(r"^.*?@", "", ctx.email)
        for d in settings.FIX_EMAILS.keys():
            if email_domain in settings.FIX_EMAILS[d]:
                ctx.email = re.sub(rf"{email_domain}$", d, ctx.email)
        return ctx
