import json
import logging

from app.core.config import settings


class EndpointFilter(logging.Filter):
    def __init__(self, excluded_endpoints: list[str]) -> None:
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args and len(record.args) >= 3:
            endpoint: str | None = None

            if isinstance(record.args, tuple):
                endpoint = str(record.args[2])

            return endpoint not in self.excluded_endpoints

        return False


class StripSecret(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if isinstance(msg, (list, dict)):
            msg = json.dumps(msg)
        elif isinstance(msg, str):
            msg = str(msg)

        return msg.replace("\n", ""), kwargs


def create_log_adapter():
    excluded_endpoints = ["/metrics"]

    log_format_2 = (
        '{"time": "%(asctime)s", "process": "%(process)d:%(threadName)s", '
        '"name": "%(name)s", "levelname": "%(levelname)s", '
        '"message": "%(message)s | %(filename)s:%(lineno)d"}'
    )

    logging.getLogger('hpack').setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO, format=log_format_2)

    if settings.use_excluded_endpoints:
        logger = logging.getLogger("uvicorn.access")
        logger.addFilter(EndpointFilter(excluded_endpoints))
    else:
        logger = logging.getLogger("online log")

    logger.setLevel(logging.DEBUG)
    adapter = StripSecret(logger, {})

    return adapter


log: logging.Logger = create_log_adapter()
