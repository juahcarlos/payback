import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import AsyncIterator
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.core.database import create_session
from app.domain.payments import PaymentSystem
from app.models import Coupons, Transactions, Users
from app.repositories.coupons import CouponDBRepo
from app.repositories.transactions import TransactionDBRepo
from app.repositories.users import UserDBRepo
from app.services.payments.base import PaymentService
from app.utils.datetime import utc_now_naive


@dataclass(frozen=True)
class PaymentRecords:
    email: str
    coupon_code: str
    transaction_id: int
    fixed_now: int


@asynccontextmanager
async def payment_records() -> AsyncIterator[PaymentRecords]:
    token = uuid4().hex
    email = f"payment-finalization-{token}@example.test"
    coupon_code = f"PAY{token}"
    access_code = f"CODE{token}"
    user_coupon = f"USER{token}"
    now = utc_now_naive()
    fixed_now = int(datetime.now(UTC).timestamp())

    async with create_session() as session:
        async with session.begin():
            user = Users(
                email=email,
                created=now,
                cn=f"sec-test-{token}",
                trial=False,
                version_page=0,
                code=access_code,
                coupon=user_coupon,
                expires=fixed_now - 100,
                plan=0,
                country_iso="us",
                password="test-password",
                reg_source="web",
                dubious=False,
                subscribed=False,
                lang="en",
            )
            coupon = Coupons(
                coupon=coupon_code,
                max_use_limit=10,
                percent=10,
                prolong=25,
                times_used=0,
                manual=False,
                expiration=now + timedelta(days=30),
                description="integration test",
                created=now,
            )
            transaction = Transactions(
                system=PaymentSystem.CRYPTOMUS,
                days=30,
                amount=10,
                email=email,
                expires=now + timedelta(days=3),
                created=now,
                trial=False,
                coupon=coupon_code,
                version_page=2,
                country_iso="us",
                complete=False,
                partner_id=0,
                partner_referrer_id=0,
                refund=False,
            )
            session.add_all([user, coupon, transaction])
            await session.flush()
            transaction_id = transaction.id

    records = PaymentRecords(
        email=email,
        coupon_code=coupon_code,
        transaction_id=transaction_id,
        fixed_now=fixed_now,
    )
    try:
        yield records
    finally:
        async with create_session() as session:
            async with session.begin():
                await session.execute(
                    delete(Transactions).where(Transactions.email == email)
                )
                await session.execute(delete(Users).where(Users.email == email))
                await session.execute(
                    delete(Coupons).where(Coupons.coupon == coupon_code)
                )


class NoOpPaymentNotifications:
    async def send_new_user_email(self, **_: object) -> None:
        return None

    async def servers_update(self, *_: object) -> None:
        return None


async def unexpected_access_code() -> str:
    raise AssertionError("test user already has an access code")


def make_payment_service() -> PaymentService:
    return PaymentService(
        redis=None,
        buy_service=None,
        email_service=NoOpPaymentNotifications(),
        ipinfo_service=None,
        user_service=SimpleNamespace(repo=UserDBRepo()),
        code_service=SimpleNamespace(create_access_code=unexpected_access_code),
        cookie_service=None,
        coupon_service=SimpleNamespace(repo=CouponDBRepo()),
        server_update_service=NoOpPaymentNotifications(),
        translation_service=None,
        tariff_repo=None,
        partner_repo=None,
        trans_repo=TransactionDBRepo(),
        locale="en",
    )


async def read_payment_records(records: PaymentRecords) -> tuple[Users, Transactions, Coupons]:
    async with create_session() as session:
        user = await session.scalar(select(Users).where(Users.email == records.email))
        transaction = await session.scalar(
            select(Transactions).where(Transactions.id == records.transaction_id)
        )
        coupon = await session.scalar(
            select(Coupons).where(Coupons.coupon == records.coupon_code)
        )
        assert user is not None
        assert transaction is not None
        assert coupon is not None
        return user, transaction, coupon


@pytest.mark.anyio
async def test_finish_payment_is_atomic_and_idempotent(
    monkeypatch: pytest.MonkeyPatch,
    unpooled_test_database,
) -> None:
    async with payment_records() as records:
        monkeypatch.setattr(
            "app.services.payments.base.time.time",
            lambda: records.fixed_now,
        )
        service = make_payment_service()

        await service.finish_payment(records.transaction_id, PaymentSystem.CRYPTOMUS)
        await service.finish_payment(records.transaction_id, PaymentSystem.CRYPTOMUS)
        await asyncio.sleep(0)

        user, transaction, coupon = await read_payment_records(records)
        expected_expiration = (
            records.fixed_now
            + 30 * PaymentService.SECONDS_IN_A_DAY
            + int(30 * PaymentService.SECONDS_IN_A_DAY * 25 / 100)
        )
        assert user.expires == expected_expiration
        assert transaction.complete is True
        assert transaction.expires == datetime.fromtimestamp(
            expected_expiration,
            tz=UTC,
        ).replace(tzinfo=None)
        assert coupon.times_used == 1


@pytest.mark.anyio
async def test_finish_payment_concurrent_callbacks_apply_once(
    monkeypatch: pytest.MonkeyPatch,
    unpooled_test_database,
) -> None:
    async with payment_records() as records:
        monkeypatch.setattr(
            "app.services.payments.base.time.time",
            lambda: records.fixed_now,
        )
        service = make_payment_service()

        await asyncio.gather(
            service.finish_payment(records.transaction_id, PaymentSystem.CRYPTOMUS),
            service.finish_payment(records.transaction_id, PaymentSystem.CRYPTOMUS),
        )
        await asyncio.sleep(0)

        user, transaction, coupon = await read_payment_records(records)
        expected_expiration = (
            records.fixed_now
            + 30 * PaymentService.SECONDS_IN_A_DAY
            + int(30 * PaymentService.SECONDS_IN_A_DAY * 25 / 100)
        )
        assert user.expires == expected_expiration
        assert transaction.complete is True
        assert coupon.times_used == 1


@pytest.mark.anyio
async def test_finish_payment_rolls_back_every_database_change_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    unpooled_test_database,
) -> None:
    async with payment_records() as records:
        monkeypatch.setattr(
            "app.services.payments.base.time.time",
            lambda: records.fixed_now,
        )
        service = make_payment_service()
        coupon_repo = service.coupon_service.repo
        increment_coupon_times_used = coupon_repo.increment_coupon_times_used

        async def increment_then_fail(*, session, coupon_code: str) -> None:
            await increment_coupon_times_used(
                session=session,
                coupon_code=coupon_code,
            )
            raise RuntimeError("injected failure after coupon update")

        monkeypatch.setattr(
            coupon_repo,
            "increment_coupon_times_used",
            increment_then_fail,
        )

        with pytest.raises(RuntimeError, match="injected failure"):
            await service.finish_payment(records.transaction_id, PaymentSystem.CRYPTOMUS)

        user, transaction, coupon = await read_payment_records(records)
        assert user.expires == records.fixed_now - 100
        assert transaction.complete is False
        assert coupon.times_used == 0
