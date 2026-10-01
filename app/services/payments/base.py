import asyncio
import re
import time
from datetime import UTC, datetime, timedelta

from fastapi import Depends
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import exceptions as app_exceptions
from app.core.config import settings
from app.core.locale import get_current_locale
from app.core.logs import log
from app.core.redis import get_redis
from app.domain.payments import PaymentData, PaymentSuccess, PaymentSystem
from app.domain.servers import UserServerData
from app.domain.transactions import TransactionSaveModel
from app.domain.users import UserPaymentInputData, UserReadModel
from app.models import Transactions, Users
from app.repositories import (
    PartnerDBRepo,
    TariffDBRepo,
    TransactionDBRepo,
    get_partner_repo,
    get_tariff_repo,
    get_transaction_repo,
)
from app.services import (
    BuyService,
    CodeService,
    CookieService,
    CouponService,
    EmailService,
    IPInfoService,
    ServerUpdateService,
    TranslationService,
    UserService,
    get_buy_service,
    get_code_service,
    get_cookie_service,
    get_coupon_service,
    get_email_service,
    get_ipinfo_service,
    get_server_update_service,
    get_translation_service,
    get_user_service,
)
from app.utils.datetime import as_utc_naive, utc_now_naive


# TODO: separate create, success,...

class PaymentService:
    SECONDS_IN_A_DAY = 86400

    def __init__(
            self,
            redis: Redis,
            buy_service: BuyService,
            email_service: EmailService,
            ipinfo_service: IPInfoService,
            user_service: UserService,
            code_service: CodeService,
            cookie_service: CookieService,
            coupon_service: CouponService,
            server_update_service: ServerUpdateService,
            translation_service: TranslationService,
            tariff_repo: TariffDBRepo,
            partner_repo: PartnerDBRepo,
            trans_repo: TransactionDBRepo,
            locale: str,
    ) -> None:
        self.redis = redis
        self.buy_service = buy_service
        self.email_service = email_service
        self.ipinfo_service = ipinfo_service
        self.user_service = user_service
        self.code_service = code_service
        self.cookie_service = cookie_service
        self.coupon_service = coupon_service
        self.server_update_service = server_update_service
        self.translation_service = translation_service
        self.tariff_repo = tariff_repo
        self.trans_repo = trans_repo
        self.partner_repo = partner_repo
        self.locale = locale

    async def _check_email_domain(self, email: str) -> None:
        email_domain = re.sub(r'^.*?@', '', email)
        if await self.redis.exists(f"blacklist:email:{email_domain}"):
            log.warning("PaymentService: email domain %s is in the blacklist", email_domain)
            raise app_exceptions.ErrorBlacklistedEmail()

    async def _check(self, data: PaymentData) -> None:
        if not self.buy_service.check_hidden_captcha(
                ip=data.ip,
                hidden_captcha=data.hidden_captcha,
        ):
            log.warning("PaymentService: wrong hidden captcha")
            raise app_exceptions.ClientError(error_code="error.wrong.captcha")

        await self._check_email_domain(data.email)

    async def _calculate_amount_with_coupon(
            self,
            coupon: str | None,
            plan: str,
            system: PaymentSystem,
    ) -> float:
        plan_from_db = await self.tariff_repo.get_tariff_by_plan(plan)
        if not plan_from_db:
            raise app_exceptions.ClientError()

        amount = float(plan_from_db.countTextSum)

        if coupon:
            coupon_from_db = await self.coupon_service.get_coupon_by_code(coupon)
            if coupon_from_db:
                amount *=  (100 - coupon_from_db.percent) / 100

        return round(amount, 2)

    async def _calculate_partner_amount(self, partner_id: int, trans_amount: float) -> float:
        partner = await self.partner_repo.get_partner_by_id(partner_id)
        if not partner:
            return 0

        partner_amount = round(trans_amount * partner.commission / 100, 2)
        return partner_amount

    async def create(self, data: PaymentData) -> TransactionSaveModel:
        await self._check(data)

        country_iso = self.ipinfo_service.get_country_iso(data.ip)

        amount = await self._calculate_amount_with_coupon(
            coupon=data.coupon,
            plan=data.plan,
            system=data.system,
        )

        log.debug(
            "PaymentService create: calculated amount = %s (email = %s)",
            str(amount),
            data.email,
        )

        user = await self.user_service.get_or_create_user(
            UserPaymentInputData(
                email=data.email,
                country_iso=country_iso or "us",
                amount=amount,
            )
        )

        system = data.system
        trans_data = TransactionSaveModel(
            system=system,
            days=int(data.plan),
            amount=amount,
            email=data.email,
            created=utc_now_naive(),
            expires=utc_now_naive() + timedelta(days=3),
            coupon=data.coupon,
            country_iso=country_iso or "us",
            complete=False,
            partner_id=user.partner_id or 0,
            refund=False,
        )

        if trans_data.partner_id:
            trans_data.partner_amount = await self._calculate_partner_amount(
                partner_id=trans_data.partner_id,
                trans_amount=trans_data.amount,
            )
            log.debug(
                "PaymentService create: calculated partner amount = %s (email = %s)",
                str(trans_data.partner_amount),
                data.email,
            )

        return trans_data

    async def _update_user_subscription(
            self,
            trans: Transactions,
            user_row: Users,
            session: AsyncSession,
    ) -> UserReadModel:
        code = user_row.code
        if not code:
            code = await self.code_service.create_access_code()

        user_coupon = user_row.coupon
        if not user_coupon:
            coupon = await self.coupon_service.generate_new_coupon(discount=10, days_valid=30)
            user_coupon = coupon.coupon

        user_trial = bool(user_row.trial and trans.trial)
        now_unix = int(time.time())
        elapsed_time = 0
        user_current_expires = user_row.expires
        if user_current_expires and user_current_expires > now_unix and not user_trial:
            elapsed_time = user_current_expires - now_unix

        transaction_days = trans.days
        if transaction_days is None:
            log.error("PaymentService: transaction %d has no subscription duration", trans.id)
            raise app_exceptions.InternalError()

        user_expires = now_unix + transaction_days * self.SECONDS_IN_A_DAY + elapsed_time
        transaction_coupon = trans.coupon

        if transaction_coupon:
            trans_coupon = await self.coupon_service.repo.get_coupon_by_code_in_session(
                session=session,
                coupon_code=transaction_coupon,
            )
            if trans_coupon and trans_coupon.prolong is not None and trans_coupon.prolong > 0:
                user_expires += int(
                    transaction_days
                    * self.SECONDS_IN_A_DAY
                    * trans_coupon.prolong
                    / 100
                )
            await self.coupon_service.repo.increment_coupon_times_used(
                session=session,
                coupon_code=transaction_coupon,
            )

        user_row.code = code
        user_row.coupon = user_coupon
        user_row.trial = user_trial
        user_row.expires = user_expires
        user_row.plan = transaction_days
        trans.expires = as_utc_naive(datetime.fromtimestamp(user_expires, tz=UTC))

        return UserReadModel(
            **{
                column.key: getattr(user_row, column.key)
                for column in Users.__table__.columns
            }
        )

    async def finish_payment(
            self,
            payment_id: int,
            payment_system: PaymentSystem,
    ) -> None:
        user: UserReadModel | None = None
        async with self.trans_repo.create_session() as session:
            async with session.begin():
                trans = await self.trans_repo.get_transaction_for_update(
                    session=session,
                    transaction_id=payment_id,
                )
                if not trans:
                    log.warning(
                        "PaymentService: finish_payment - no transaction (payment_id = %s)",
                        str(payment_id),
                    )
                    return

                if trans.complete:
                    log.info(
                        "PaymentService: finish_payment - transaction already completed "
                        "(payment_id = %s)",
                        str(payment_id),
                    )
                    return

                user_row = await self.user_service.repo.get_user_by_email_for_update(
                    session=session,
                    email=trans.email or "",
                )
                if not user_row:
                    log.warning(
                        "PaymentService: finish_payment - no user (trans = %d)",
                        trans.id,
                    )
                    return

                user = await self._update_user_subscription(
                    trans=trans,
                    user_row=user_row,
                    session=session,
                )
                trans.complete = True
                await session.flush()


        email_task = asyncio.create_task(
            self.email_service.send_new_user_email(
                user_data=user,
                payment_system=payment_system,
            )
        )
        def callback(t: asyncio.Task) -> None:
            try:
                t.result()
            except app_exceptions.InternalError as e:
                log.error("PaymentService: send_new_user_email task failed (%s)", e)

        email_task.add_done_callback(callback)

        user_data = UserServerData(
            cn=user.cn,
            expires=user.expires,
            password=user.password,
        )
        servers_task = asyncio.create_task(self.server_update_service.servers_update(user_data))
        servers_task.add_done_callback(lambda t: t.result())

    async def success(self, email_cookie: str | None = None) -> PaymentSuccess:
        if not email_cookie:
            return PaymentSuccess(
                message="Cookies are switched off or session has been terminated",
            )

        email = self.cookie_service.decrypt(email_cookie)

        if not email:
            return PaymentSuccess(
                message=f"User was not found by email {email}",
            )

        message = PaymentSuccess()

        user = await self.user_service.get_user_by_email(email)
        if not user:
            raise app_exceptions.Error404()

        if user.country_iso == 'ru' and self.locale != 'ru':
            message.country_iso = user.country_iso

            self.locale = 'ru'
            message.url_redirect = (
                f"{settings.frontend_base_url}/{self.locale}"
                f"/vpn/payment/success?email_cookie={email_cookie}"
            )

        if user.trial:
            msg_1 = self.translation_service.translate_message(
                "vpn.payment.done.thanks-trial",
                locale=self.locale,
            )
            msg_2 = self.translation_service.translate_message(
                "vpn.payment.done.activated-trial",
                locale=self.locale,
            )
            msg = f"{msg_1}\n\n{msg_2}"
        else:
            msg_1 = self.translation_service.translate_message(
                "vpn.payment.done.thanks-paid",
                locale=self.locale,
            )
            msg_2 = self.translation_service.translate_message(
                "vpn.payment.done.activated-paid",
                locale=self.locale,
            )
            msg_3 = self.translation_service.translate_message(
                "vpn.payment.done.activated-paid-info",
                locale=self.locale,
            )
            msg = f"{msg_1}\n\n{msg_2}\n\n{msg_3}"

        message.message = msg
        message.email = user.email
        message.code = user.code

        return message


def get_payment_service(
        redis: Redis = Depends(get_redis),  # noqa: B008
        buy_service: BuyService = Depends(get_buy_service),  # noqa: B008
        email_service: EmailService = Depends(get_email_service),  # noqa: B008
        ipinfo_service: IPInfoService = Depends(get_ipinfo_service),  # noqa: B008
        user_service: UserService = Depends(get_user_service),  # noqa: B008
        code_service: CodeService = Depends(get_code_service),  # noqa: B008
        cookie_service: CookieService = Depends(get_cookie_service),  # noqa: B008
        coupon_service: CouponService = Depends(get_coupon_service),  # noqa: B008
        server_update_service: ServerUpdateService = Depends(get_server_update_service),  # noqa: B008
        translation_service: TranslationService = Depends(get_translation_service),  # noqa: B008
        tariff_repo: TariffDBRepo = Depends(get_tariff_repo),  # noqa: B008
        partner_repo: PartnerDBRepo = Depends(get_partner_repo),  # noqa: B008
        trans_repo: TransactionDBRepo = Depends(get_transaction_repo),  # noqa: B008
        locale: str = Depends(get_current_locale),
) -> PaymentService:
    return PaymentService(
        redis=redis,
        buy_service=buy_service,
        email_service=email_service,
        ipinfo_service=ipinfo_service,
        user_service=user_service,
        code_service=code_service,
        cookie_service=cookie_service,
        coupon_service=coupon_service,
        server_update_service=server_update_service,
        translation_service=translation_service,
        tariff_repo=tariff_repo,
        partner_repo=partner_repo,
        trans_repo=trans_repo,
        locale=locale,
    )
