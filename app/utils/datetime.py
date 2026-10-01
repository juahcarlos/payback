from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_now_naive() -> datetime:
    return utc_now().replace(tzinfo=None)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def as_utc_naive(value: datetime) -> datetime:
    return as_utc(value).replace(tzinfo=None)


def utc_timestamp(value: datetime) -> int:
    return int(as_utc(value).timestamp())
