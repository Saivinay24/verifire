"""Lookup (brief, Appendix A.3): one cached row plus a short evidence list. No reporter data leaves here."""

import threading
import time
from typing import Any

from app.db import get_engine
from app.domain.catalog import verified_owner
from app.domain.identifiers import IdentifierType, mask, normalise, parse_type
from app.domain.timefmt import fmt
from app.domain.trust import Verdict
from app.repos import store

EVIDENCE_LIMIT = 20

# Answers are cached in this process and dropped on every write (report, challenge, reset). A write
# bumps the generation after it commits, so an answer read before the write is never served after
# it. Correct for one server process, which is how the service runs (see render.yaml).
CACHE_TTL_SECONDS = 60.0
CACHE_MAX = 5000
_cache: dict[tuple[int, str, str], tuple[float, dict[str, Any]]] = {}
_generation = 0
_lock = threading.Lock()


def invalidate() -> None:
    global _generation
    with _lock:
        _generation += 1
        _cache.clear()


def lookup(raw_type: str, raw_value: str) -> dict[str, Any]:
    id_type: IdentifierType = parse_type(raw_type)
    value = normalise(id_type, raw_value)  # InvalidIdentifier -> 400 at the API layer
    key = (_generation, id_type.value, value)
    hit = _cache.get(key)
    if hit and time.monotonic() - hit[0] < CACHE_TTL_SECONDS:
        return hit[1]
    answer = _answer(id_type, value)
    with _lock:
        if key[0] == _generation:
            if len(_cache) >= CACHE_MAX:
                _cache.clear()
            _cache[key] = (time.monotonic(), answer)
    return answer


def _answer(id_type: IdentifierType, value: str) -> dict[str, Any]:
    owner = verified_owner(id_type, value)
    verified = owner is not None
    with get_engine().connect() as conn:
        row = store.get_identifier(conn, id_type, value)
        evidence = (
            store.recent_evidence(conn, row["id"], EVIDENCE_LIMIT, after=row["cleared_before"])
            if row and row["report_count"]
            else []
        )

    if row is None or row["report_count"] == 0:
        return {
            "verdict": (Verdict.VERIFIED_BUSINESS if verified else Verdict.NO_REPORTS).value,
            "report_count": 0,
            "distinct_reporters": 0,
            "first_seen": None,
            "last_seen": None,
            "scam_type": None,
            "scam_types": [],
            "display_value": value if verified else mask(id_type, value),
            "evidence": [],
            "challenged": bool(row and row["challenged"]),
            "dispute": _dispute(row),
            "verified_owner": owner,
            "summary": summary(Verdict.VERIFIED_BUSINESS if verified else Verdict.NO_REPORTS, 0),
        }
    return {
        "verdict": row["verdict"],
        "report_count": row["report_count"],
        "distinct_reporters": row["distinct_reporters"],
        "first_seen": fmt(row["first_seen"]),
        "last_seen": fmt(row["last_seen"]),
        "scam_type": row["top_scam_type"],
        # Every type people reported, one vote per counted person; scam_type is the first.
        "scam_types": (row["explain"] or {}).get("types", []),
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
        "dispute": _dispute(row),
        # Extra fields are allowed by the brief; these explain the verdict without exposing anyone.
        "trust_score": row["trust_score"],
        "verified_owner": owner,
        "summary": summary(row["verdict"], row["distinct_reporters"]),
    }


def _dispute(row: Any) -> dict[str, Any] | None:
    """The dispute's state and deadline (extra field). Never who asked or why."""
    return (row["explain"] or {}).get("dispute") if row is not None else None


def summary(verdict: str, people: int) -> str:
    """Neutral wording only (privacy rule 3): what people reported, never what someone is."""
    if verdict == Verdict.VERIFIED_BUSINESS:
        return "Verified business or official helpline"
    if people == 0:
        return "No reports yet"
    noun = "person" if people == 1 else "people"
    return f"Reported by {people} {noun} near you"
