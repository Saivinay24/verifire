"""Signed licence files (brief, "Ship it").

A licence says who may use the server and until when. It is signed with an Ed25519 private key
that never leaves the vendor's laptop; the server holds only the public key below, so editing
any field (the expiry date, the licensee) breaks the signature.

File format (JSON):
    {"licence_id": "...", "licensee": "Demo Bank", "issued_at": "...+05:30",
     "expires_at": "...+05:30", "signature": "<base64 Ed25519 over the canonical payload>"}

Canonical payload = the four non-signature fields as JSON with sorted keys and no spaces.
"""

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Any

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from app.domain.timefmt import InvalidTime, parse

PUBLIC_KEY_B64 = "ObHomNfpRXDvfnz9TUfsUYsXhseXfPI7Hpxe431rbww="
SIGNED_FIELDS = ("licence_id", "licensee", "issued_at", "expires_at")
# Clocks drift a little (NTP); only a jump backwards larger than this is treated as tampering.
CLOCK_TOLERANCE = timedelta(minutes=5)


class InvalidLicence(ValueError):
    pass


class Status(StrEnum):
    VALID = "valid"
    EXPIRED = "expired"
    MISSING = "missing"
    CLOCK_ROLLBACK = "clock_rollback"


@dataclass(frozen=True)
class Licence:
    licence_id: str
    licensee: str
    issued_at: datetime
    expires_at: datetime
    raw: dict[str, str]


def canonical_payload(fields: dict[str, Any]) -> bytes:
    return json.dumps({k: fields[k] for k in SIGNED_FIELDS}, sort_keys=True, separators=(",", ":")).encode()


def verify(document: Any, public_key_b64: str | None = None) -> Licence:
    """Check shape and signature. Raises InvalidLicence on anything a tamperer could produce."""
    if not isinstance(document, dict):
        raise InvalidLicence("licence must be a JSON object")
    missing = [k for k in (*SIGNED_FIELDS, "signature") if not isinstance(document.get(k), str)]
    if missing:
        raise InvalidLicence(f"licence is missing {', '.join(missing)}")
    try:
        signature = base64.b64decode(document["signature"], validate=True)
        VerifyKey(base64.b64decode(public_key_b64 or PUBLIC_KEY_B64)).verify(
            canonical_payload(document), signature
        )
    except (BadSignatureError, binascii.Error, ValueError) as exc:
        raise InvalidLicence("licence signature is not valid") from exc
    try:
        issued_at, expires_at = parse(document["issued_at"]), parse(document["expires_at"])
    except InvalidTime as exc:
        raise InvalidLicence("licence dates are not valid") from exc
    return Licence(
        licence_id=document["licence_id"],
        licensee=document["licensee"],
        issued_at=issued_at,
        expires_at=expires_at,
        raw={k: document[k] for k in (*SIGNED_FIELDS, "signature")},
    )


def status(licence: Licence | None, now: datetime, high_water: datetime | None) -> Status:
    if licence is None:
        return Status.MISSING
    # Setting the clock back must not revive an expired licence (brief, "Bonus thinking").
    if high_water is not None and now < high_water - CLOCK_TOLERANCE:
        return Status.CLOCK_ROLLBACK
    if now < licence.issued_at - CLOCK_TOLERANCE:
        return Status.CLOCK_ROLLBACK
    if now >= licence.expires_at:
        return Status.EXPIRED
    return Status.VALID
