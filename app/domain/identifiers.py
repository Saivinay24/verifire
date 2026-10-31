"""Canonical forms for the four identifier types (brief, Appendix A rule 3).

Every report and lookup goes through `normalise` so that `+91 98765 43210`, `09876543210`
and `98765-43210` are one key. Junk is rejected here, by the *shape* of the value only;
no rule in this module names a specific identifier.
"""

import itertools
import re
import unicodedata
from enum import StrEnum
from urllib.parse import unquote, urlsplit


class IdentifierType(StrEnum):
    PHONE = "phone"
    UPI = "upi"
    URL = "url"
    SENDER_ID = "sender_id"


class InvalidIdentifier(ValueError):
    """The value cannot be a real identifier of the given type (HTTP 400)."""


# Direction and zero-width marks that phone call logs and chat apps paste along with numbers.
_INVISIBLE = dict.fromkeys(
    map(ord, "\u200b\u200c\u200d\u200e\u200f\u202a\u202b\u202c\u202d\u202e\u2060\ufeff")
)
_PHONE_SEPARATORS = re.compile("[\\s\\-().\u00a0]")
_UPI = re.compile(r"^[a-z0-9._-]{2,256}@[a-z][a-z0-9.]{1,63}$")
_HOST = re.compile(r"^(?=.{4,253}$)([a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$")
_SENDER_PREFIX = re.compile(r"^[A-Z]{2}-")
_SENDER_SUFFIX = re.compile(r"-[PSTG]$")
_SENDER = re.compile(r"^[A-Z]{6}$")


def _clean(raw: str) -> str:
    return unicodedata.normalize("NFKC", raw).translate(_INVISIBLE).strip()


def _is_run(digits: str) -> bool:
    """Ascending or descending consecutive digits, e.g. 1234567890 or 9876543210 (keyboard junk)."""
    steps = {(int(b) - int(a)) % 10 for a, b in itertools.pairwise(digits)}
    return steps in ({1}, {9})


def normalise_phone(raw: str) -> str:
    value = _PHONE_SEPARATORS.sub("", _clean(raw))
    if value.startswith("+"):
        value = value[1:]
        if not value.startswith("91"):
            raise InvalidIdentifier("only Indian (+91) numbers are supported")
    if not value.isdigit():
        raise InvalidIdentifier("a phone number contains only digits")

    # Short helplines (1930, 1909, 14440) and toll-free 1800/1860 lines keep their own form.
    # Appendix C has both `1800 1600` (8 digits) and `1860 419 5555` (11 digits).
    if value.startswith(("1800", "1860")) and 8 <= len(value) <= 11:
        return value
    if value.startswith("1") and 3 <= len(value) <= 6:
        if len(value) >= 4 and (_is_run(value) or len(set(value)) < 2):
            raise InvalidIdentifier("not a valid short code")  # `12345`, `1111`
        return value

    if value.startswith("0091") and len(value) == 14:
        value = value[4:]
    elif value.startswith("91") and len(value) == 12:
        value = value[2:]
    elif value.startswith("0") and len(value) == 11:
        value = value[1:]
    if len(value) != 10:
        raise InvalidIdentifier("a phone number has 10 digits after +91")
    # Indian numbers (mobiles 6-9, landlines with STD code 2-5) never start with 0 or 1.
    if value[0] in "01":
        raise InvalidIdentifier("not a valid Indian number")
    # Not `_is_run`: the brief's own example, 9876543210, is a descending run.
    if len(set(value)) < 3:
        raise InvalidIdentifier("not a real number")
    return "+91" + value


def normalise_upi(raw: str) -> str:
    value = _clean(raw)
    lowered = value.lower()
    if lowered.startswith("upi://pay?"):
        # A scanned QR code: the payee address is the `pa` parameter.
        params = dict(p.split("=", 1) for p in value.split("?", 1)[1].split("&") if "=" in p)
        value = unquote(params.get("pa", ""))
    value = re.sub(r"\s+", "", value).lower()
    if value.count("@") != 1 or not _UPI.match(value):
        raise InvalidIdentifier("a UPI ID looks like name@bank")
    return value


def normalise_url(raw: str) -> str:
    value = _clean(raw)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", value):
        value = "https://" + value
    parts = urlsplit(value)
    if parts.scheme.lower() not in ("http", "https"):
        raise InvalidIdentifier("a link starts with http:// or https://")
    host = (parts.hostname or "").rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    if not _HOST.match(host):
        # Rejects `test`, `localhost`, raw IP addresses and hosts with no real top-level domain.
        raise InvalidIdentifier("a link needs a real domain like example.in")
    path = parts.path.rstrip("/")
    return f"https://{host}{path}"


def normalise_sender(raw: str) -> str:
    value = re.sub(r"\s+", "", _clean(raw)).upper()
    value = _SENDER_SUFFIX.sub("", _SENDER_PREFIX.sub("", value))
    if not _SENDER.match(value):
        raise InvalidIdentifier("an SMS sender is a 6-letter code like HDFCBK")
    return value


_NORMALISERS = {
    IdentifierType.PHONE: normalise_phone,
    IdentifierType.UPI: normalise_upi,
    IdentifierType.URL: normalise_url,
    IdentifierType.SENDER_ID: normalise_sender,
}


def parse_type(raw: str) -> IdentifierType:
    try:
        return IdentifierType(raw.strip().lower())
    except ValueError as exc:
        raise InvalidIdentifier("type must be phone, upi, url or sender_id") from exc


def normalise(id_type: IdentifierType, raw: str) -> str:
    if not raw or not raw.strip():
        raise InvalidIdentifier("value is empty")
    if len(raw) > 512:
        raise InvalidIdentifier("value is too long")
    return _NORMALISERS[id_type](raw)


def mask(id_type: IdentifierType, value: str) -> str:
    """Public form of an identifier that fewer than 3 independent people reported (privacy rule 2)."""
    if id_type is IdentifierType.PHONE:
        digits = value.removeprefix("+91")
        if len(digits) < 6:
            return digits[0] + "X" * (len(digits) - 1)
        return digits[:2] + "X" * (len(digits) - 5) + digits[-3:]
    if id_type is IdentifierType.UPI:
        name, _, handle = value.partition("@")
        return f"{name[:1]}***@{handle}"
    if id_type is IdentifierType.URL:
        host = value.removeprefix("https://").split("/", 1)[0]
        labels = host.split(".")
        return f"{labels[0][:3]}***.{labels[-1]}/..."
    return value[:2] + "****"
