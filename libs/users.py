from datetime import datetime
from typing import Annotated, Optional

from fastapi import Depends

from config import settings
from dbm.database import DbQuery, db
from dbm.schemas import MailSource, User, UserFull, UserId, UserInsertEmail
from libs.exceptions import internal_error
from libs.ip_info import get_country_iso
from libs.logs import log
from libs.send_mail import send_code
from libs.utils import code_for_user, generate_password


async def insert_user(
    data: MailSource,
    db: Annotated[DbQuery, Depends(db)],
    ip: Optional[str] = None,
    lang: Optional[str] = "en",
):
    code = await code_for_user(db)

    data_insert = User(
        email=data.email,
        trial=True,
        code=code,
        created=datetime.now(),
        version_page=2,
        expires=int(datetime.now().strftime("%s")) + 3600 * 24 * 365 * 5,
        password=generate_password(),
        reg_source=data.source,
        country_iso=get_country_iso(ip),
        lang=lang,
    )

    await db.create_user(data_insert)
    user = await db.get_user_by_email(data.email)

    if user is None:
        log.error(f"ERROR inserting email user {user}")
        raise internal_error(lang, "error inserting email")

    return user


# send email
async def send_letter(
    db: Annotated[DbQuery, Depends(db)],
    user: UserId,
    lang: str,
    subject: str,
    amount: int = 0,
):
    await send_code(user, db, subject)


async def create_user(
    data: MailSource,
    db: Annotated[DbQuery, Depends(db)],
    ip: Optional[str] = None,
    lang: Optional[str] = "en",
    subject: Optional[str] = settings.NEW_USER_SUBJECT,
    amount: int = 0,
):
    user = await insert_user(data, db, ip, lang)
    await send_letter(db, user, lang, subject, amount)
    return user


async def get_user_response(db: Annotated[DbQuery, Depends(db)], user: UserId):
    user_response = UserFull(
        email=user.email,
        created=user.created.strftime("%Y-%m-%d %H:%M:%S"),
        cn=user.cn,
        trial=user.trial,
        version_page=user.version_page,
        code=user.code,
        coupon=user.coupon,
        expires=str(user.expires),
        plan=user.plan,
        country_iso=user.country_iso,
        password=user.password,
        reg_source=user.reg_source,
        dubious=user.dubious,
        subscribed=int(user.subscribed is True),
        lang=user.lang,
        partner_id=user.partner_id,
        note=user.note,
        status="OK",
    )

    return user_response


async def insert_mail(
    data: MailSource,
    db: Annotated[DbQuery, Depends(db)],
    ip: str,
    lang: Optional[str] = "en",
    subject: Optional[str] = settings.NEW_USER_SUBJECT,
    amount: int = 0,
) -> UserInsertEmail:
    has_user = True
    user = await db.get_user_by_email(data.email)

    if not user:
        has_user = False
        user = await create_user(data, db, ip, lang, subject, amount)

    user_response = await get_user_response(db, user)

    response = UserInsertEmail(**user_response.model_dump())
    response.has_user = has_user

    return response
