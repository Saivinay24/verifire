"""Time parsing and formatting. Times in the API look like 2026-10-27T18:21:04+05:30 (brief, rule 1)."""

from datetime import datetime
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


class InvalidTime(ValueError):
    pass


def parse(raw: object) -> datetime:
    if not isinstance(raw, str) or not raw.strip():
        raise InvalidTime("time is missing")
    try:
        value = datetime.fromisoformat(raw.strip())
    except ValueError as exc:
        raise InvalidTime("time must look like 2026-10-27T18:21:04+05:30") from exc
    if value.tzinfo is None:
        raise InvalidTime("time needs a timezone offset like +05:30")
    return value


def fmt(value: datetime | None) -> str | None:
    return None if value is None else value.astimezone(IST).isoformat(timespec="seconds")
