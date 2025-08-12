import json
import logging

from config import settings


class EndpointFilter(logging.Filter):
    """Filter class to exclude specific endpoints from log entries."""

    def __init__(self, excluded_endpoints: list[str]) -> None:
        """
        Initialize the EndpointFilter class.

        Args:
            excluded_endpoints: A list of endpoints to be excluded from log entries.
        """
        self.excluded_endpoints = excluded_endpoints

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter out log entries for excluded endpoints.

        Args:
            record: The log record to be filtered.

        Returns:
            bool: True if the log entry should be included, False otherwise.
        """
        return (
            record.args
            and len(record.args) >= 3
            and record.args[2] not in self.excluded_endpoints
        )


excluded_endpoints = ["/metrics"]


class StripSecret(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        if type(msg) is list or type(msg) is dict:
            msg = json.dumps(msg)
        elif type(msg) is not str:
            msg = str(msg)
        return msg.replace("\n", ""), kwargs


def log():
    LOG_FORMAT2 = """{"time": "%(asctime)s", "process": "%(process)d:%(threadName)s",
        "name": "%(name)s", "levelname": "%(levelname)s", "message": "%(message)s
         %(filename)s:%(lineno)d"}"""

    logging.getLogger("hpack").setLevel(logging.WARNING)
    logging.basicConfig(level=logging.INFO, format=LOG_FORMAT2)

    if settings.USE_EXCLUDED_ENDPOINTS:
        logger = logging.getLogger("uvicorn.access")
        logger.addFilter(EndpointFilter(excluded_endpoints))
    else:
        logger = logging.getLogger("online log")
    logger.setLevel(logging.DEBUG)
    adapter = StripSecret(logger, {})
    return adapter


log = log()
