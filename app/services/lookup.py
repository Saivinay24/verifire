"""Lookup (brief, Appendix A.3): one cached row plus a short evidence list. No reporter data leaves here."""

from typing import Any

from app.db import get_engine
from app.domain.catalog import verified_owner
from app.domain.identifiers import IdentifierType, mask, normalise, parse_type
from app.domain.timefmt import fmt
from app.domain.trust import Verdict
from app.repos import store

EVIDENCE_LIMIT = 20


def lookup(raw_type: str, raw_value: str) -> dict[str, Any]:
    id_type: IdentifierType = parse_type(raw_type)
    value = normalise(id_type, raw_value)  # InvalidIdentifier -> 400 at the API layer
    verified = verified_owner(id_type, value) is not None
    with get_engine().connect() as conn:
        row = store.get_identifier(conn, id_type, value)
        evidence = (
            store.recent_evidence(conn, row["id"], EVIDENCE_LIMIT) if row and row["report_count"] else []
        )

    if row is None or row["report_count"] == 0:
        return {
            "verdict": (Verdict.VERIFIED_BUSINESS if verified else Verdict.NO_REPORTS).value,
            "report_count": 0,
            "distinct_reporters": 0,
            "first_seen": None,
            "last_seen": None,
            "scam_type": None,
            "display_value": value if verified else mask(id_type, value),
            "evidence": [],
            "challenged": bool(row and row["challenged"]),
        }
    return {
        "verdict": row["verdict"],
        "report_count": row["report_count"],
        "distinct_reporters": row["distinct_reporters"],
        "first_seen": fmt(row["first_seen"]),
        "last_seen": fmt(row["last_seen"]),
        "scam_type": row["top_scam_type"],
        "display_value": value if row["unmasked"] else mask(id_type, value),
        "evidence": [
            {
                "occurred_at": fmt(e["occurred_at"]),
                "channel": e["channel"],
                "scam_type": e["scam_type"],
                "pincode": e["pincode"],
            }
            for e in evidence
        ],
        "challenged": row["challenged"],
        # Extra fields are allowed by the brief; these explain the verdict without exposing anyone.
        "trust_score": row["trust_score"],
        "summary": summary(row["verdict"], row["distinct_reporters"]),
    }


def summary(verdict: str, people: int) -> str:
    """Neutral wording only (privacy rule 3): what people reported, never what someone is."""
    if verdict == Verdict.VERIFIED_BUSINESS:
        return "Verified business or official helpline"
    if people == 0:
        return "No reports yet"
    noun = "person" if people == 1 else "people"
    return f"Reported by {people} {noun} near you"
