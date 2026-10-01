from datetime import UTC, datetime, timedelta, timezone

from app.utils.datetime import as_utc, as_utc_naive, utc_now_naive, utc_timestamp


def test_utc_conversion_handles_naive_and_aware_values() -> None:
    naive_utc = datetime(2026, 1, 1, 12)
    offset_time = datetime(2026, 1, 1, 14, tzinfo=timezone(timedelta(hours=2)))

    assert as_utc(naive_utc) == datetime(2026, 1, 1, 12, tzinfo=UTC)
    assert as_utc(offset_time) == datetime(2026, 1, 1, 12, tzinfo=UTC)
    assert as_utc_naive(offset_time) == naive_utc
    assert utc_timestamp(naive_utc) == int(naive_utc.replace(tzinfo=UTC).timestamp())


def test_utc_now_naive_returns_utc_naive_datetime() -> None:
    now = utc_now_naive()

    assert now.tzinfo is None
    assert abs((now - datetime.now(UTC).replace(tzinfo=None)).total_seconds()) < 1
