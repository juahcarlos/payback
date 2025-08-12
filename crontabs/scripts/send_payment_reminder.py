import asyncio
import sys
from pathlib import Path
from typing import List

import pidfile
from parser_args import get_args_reminder

from crontabs.config_cron import settings
from crontabs.db.schemas import ReminderArgs
from crontabs.lib.mail import send_all_reminder
from crontabs.lib.utils import get_emails, get_users
from libs.logs import log

sys.path.append(str(Path(__file__).parents[0]))


args = get_args_reminder()
pid_file = args.pid or settings.PIDFILE_REMINDER


def get_args() -> ReminderArgs:
    """Get arguments from the command line interface"""
    return ReminderArgs(
        try_one_email=args.try_one_email,
        no_unsubscribe=args.no_unsubscribe,
    )


async def remind() -> List[str | None]:
    """Execute mailing to payment reminder users list."""
    args_data = get_args()
    emails = await get_emails(args_data.try_one_email)
    users = await get_users(emails, args_data.no_unsubscribe)
    log.debug(f"emails {emails}")
    res = await send_all_reminder(users)
    return res


try:
    with pidfile.PIDFile(pid_file):
        res = asyncio.run(remind())
        error = [r for r in res if r[0] != "" and r[0] is not None]

        if error is not None and error != []:
            er = [str(e) for e in error]
            err = "\n".join(er)
            log.error(f"ERROR vpn reminder {type(err)} {err}")
except pidfile.AlreadyRunningError:
    log.error("Already running")

log.info("Exiting")
