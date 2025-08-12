import hashlib
import hmac
import json
import time
from collections import OrderedDict
from typing import Annotated

import requests
from redis.asyncio.client import Redis
from config_be import settings
from dbm.redis_db import rdb
from fastapi import Depends
from jinja2 import Environment, FileSystemLoader
from lib.domain.buy.payment import Payment

from be.db.database import DbQuery, db
from be.db.schemas import FreekassaConfirmData, PaymentContext
from be.lib.domain.buy.freekassa_verify import verify
from libs.logs import log

env = Environment(loader=FileSystemLoader("templates"))


class Freekassa(Payment):
    """
    API handlers for payment processing with Freekassa payment system
    """
    def __init__(
        self,
        db: Annotated[DbQuery, Depends(db)],
        rdb: Annotated[Redis, Depends(rdb)],
    ):
        self.db = db
        self.rdb = rdb
        self.trans = None

    async def create(self, ctx: PaymentContext) -> dict:
        """
        Create or retrieve user by email via base Payment class,
        create an invoice with Freekassa,
        and return data including payment URL for redirecting user
        to the payment form on Freekassa webpage.

        Args:
            ctx: Freekassa payment data (PaymentContext).

        Returns:
            dict: Result containing payment URL, HTML form data,
                  payment ID, and status flags.
        """
        await super().create(ctx)

        amount = self.trans.amount
        payment_id = str(self.trans.id)

        res_invoice = await create_invoice(ctx, self.trans)

        if "location" not in res_invoice.keys():
            return f"Error: {res_invoice}"

        plans = json.loads(settings.PLANS)["plans"][str(self.trans.days)]
        template = env.get_template("payment-freekassa.html")
        data = template.render(
            invoice_url=res_invoice["location"],
            amount=amount,
            plans=plans,
        )
        result = {
            "error": 0,
            "useForm": 1,
            "payment_url": res_invoice["location"],
            "id": payment_id,
            "data": data,
        }
        return result

    async def confirmation(
        self,
        data: FreekassaConfirmData,
    ) -> str:
        """
        Handle Freekassa webhook confirmation of successful payment.

        Args:
            data: Freekassa webhook data for payment confirmation.

        Returns:
            str: "YES" if confirmation succeeded or error message.
        """
        trans = await self.db.get_trans_by_id(data.MERCHANT_ORDER_ID)
        verify_res = await verify(self.rdb, data, trans)

        if verify_res == 1:
            await self.full_finish_payment_by_id(data.MERCHANT_ORDER_ID)
            return "YES"

        return "ERROR: " + verify_res


@staticmethod
async def create_invoice(ctx, trans) -> str:
    """
    Create an invoice by sending transaction data to Freekassa API.

    Args:
        ctx: ctx: Freekassa payment data (PaymentContext).
        trans: Database record of a transaction with payment details.

    Returns:
        dict or str: JSON response from Freekassa API if successful,
        otherwise error message string.
    """
    time_ = str(int(time.time()))
    currency = "USD"

    hash_subject = "|".join(
        (
            str(trans.amount),
            currency,
            ctx.email,
            str(settings.FREEK_PAYMENT_SYSTEM_ID),
            ctx.ip,
            time_,
            str(trans.id),
            str(settings.FREEK_SHOP_ID),
        )
    )

    signature = hmac.new(
        settings.FREEK_API_KEY.encode("utf-8"),
        hash_subject.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    invoicedata = dict(
        OrderedDict(
            [
                ("amount", trans.amount),
                ("currency", currency),
                ("email", ctx.email),
                ("i", settings.FREEK_PAYMENT_SYSTEM_ID),
                ("ip", ctx.ip),
                ("nonce", time_),
                ("paymentId", str(trans.id)),
                ("shopId", settings.FREEK_SHOP_ID),
                ("signature", signature),
            ]
        )
    )

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Signature": signature,
    }

    try:
        res = requests.post(
            settings.FREEK_INVOICE_API_URI,
            headers=headers,
            json=invoicedata,
        ).json()
        return res
    except Exception as ex:
        msg = f"Can't request invoice by {settings.FREEK_INVOICE_API_URI} ex={ex}"
        log.error(msg)
        return msg
