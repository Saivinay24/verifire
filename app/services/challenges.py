"""Dispute (brief, Appendix A.7, bonus): a business marks its number as under review.

Under review the verdict is capped at SUSPICIOUS: never KNOWN_SCAM, but never silently cleared
either, so a real scammer cannot use a dispute to wipe their warning.
"""

import uuid
from typing import Any

from app.db import get_engine
from app.domain.catalog import verified_owner
from app.domain.identifiers import normalise, parse_type
from app.repos import store
from app.services.reports import recompute

UNDER_REVIEW = "under_review"


def _optional(payload: dict[str, Any], name: str, limit: int) -> str | None:
    value = payload.get(name)
    return value.strip()[:limit] if isinstance(value, str) and value.strip() else None


def challenge(payload: dict[str, Any]) -> dict[str, str]:
    id_type = parse_type(str(payload.get("identifier_type") or ""))
    value = normalise(id_type, str(payload.get("identifier_value") or ""))
    with get_engine().begin() as conn:
        ident = store.lock_identifier(conn, id_type, value, verified_owner(id_type, value) is not None)
        existing = store.open_challenge(conn, ident["id"])
        if existing is not None:  # One open dispute per identifier.
            return {"challenge_id": existing["id"], "status": existing["status"]}
        challenge_id = "chl_" + uuid.uuid4().hex[:12]
        store.insert_challenge(
            conn,
            {
                "id": challenge_id,
                "identifier_id": ident["id"],
                "status": UNDER_REVIEW,
                "claimant_name": _optional(payload, "claimant_name", 200),
                "contact_email": _optional(payload, "contact_email", 200),
                "proof_note": _optional(payload, "proof_note", 2000),
            },
        )
        recompute(conn, ident["id"], verified=ident["verified"], challenged=True)
    return {"challenge_id": challenge_id, "status": UNDER_REVIEW}
