"""Explore: for people researching scams, kept apart from the check-and-report flow.

Two reads, both built only from what the map and lookups already show:

- similar(text): find numbers whose reports used close wording to a pasted message. The text is
  turned into the same MinHash fingerprint stored for report notes, compared, and dropped. It is
  never stored or logged. This finds a scam script that moved to new numbers.
- known(): numbers confirmed as scams (3+ independent people, not under dispute), the same rule
  as the city sheet, with scam type, cities and dates. Never who reported, never a note.
"""

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.db import get_engine
from app.domain.areas import AREAS_BY_PINCODE
from app.domain.notes import extract, similarity
from app.domain.timefmt import fmt
from app.repos import store
from app.services.insights import public_value

# Wording search policy (not trust-engine parameters). Measured in tests/test_explore.py: the
# same script with a new number, name or amount scores 0.48 or more; other scripts and victim
# narratives stay at 0.20 or less. 0.35 sits in the gap, and still finds most half-pasted messages.
SIMILAR_MIN = 0.35
SIMILAR_LIMIT = 10
SEARCH_DAYS = 180
KNOWN_DAYS = 90
KNOWN_LIMIT = 50


class TooShort(Exception):
    """The text is too short to fingerprint: HTTP 400."""


def similar(text: str, now: datetime) -> dict[str, Any]:
    sig = extract(text[:2000]).signature
    if not sig or len(text.strip()) < 20:
        raise TooShort("paste at least a sentence of the message")
    with get_engine().connect() as conn:
        rows = store.fingerprinted_reports(conn, now - timedelta(days=SEARCH_DAYS))
    hits: dict[int, dict[str, Any]] = {}
    cities: dict[int, set[str]] = defaultdict(set)
    for r in rows:
        s = max(similarity(sig, list(r[c] or [])) for c in ("msg_sig", "note_sig"))
        if s < SIMILAR_MIN:
            continue
        verdict = "SUSPICIOUS" if r["challenged"] else r["verdict"]
        item = hits.setdefault(
            r["identifier_id"],
            {
                "identifier_type": r["id_type"],
                "display_value": public_value(r),
                "in_full": bool(r["unmasked"] or r["verified"]),
                "verdict": verdict,
                "scam_type": r["top_scam_type"],
                "people": r["distinct_reporters"],
                "last_seen": fmt(r["last_seen"]),
                "matching_reports": 0,
                "closeness": 0.0,
            },
        )
        item["matching_reports"] += 1
        item["closeness"] = max(item["closeness"], round(s, 2))
        cities[r["identifier_id"]].add(AREAS_BY_PINCODE[r["pincode"]].city)
    for key, item in hits.items():
        item["cities"] = sorted(cities[key])
    ranked = sorted(hits.values(), key=lambda h: (-h["closeness"], -h["matching_reports"]))
    return {"matches": ranked[:SIMILAR_LIMIT], "searched_days": SEARCH_DAYS}


def known(scam_type: str | None, city: str | None, now: datetime) -> dict[str, Any]:
    with get_engine().connect() as conn:
        rows = store.known_scams(conn, now - timedelta(days=KNOWN_DAYS))
    items = []
    for r in rows:
        towns = sorted({AREAS_BY_PINCODE[p].city for p in r["pincodes"] if p in AREAS_BY_PINCODE})
        if scam_type and r["top_scam_type"] != scam_type:
            continue
        if city and city not in towns:
            continue
        items.append(
            {
                "identifier_type": r["id_type"],
                "display_value": public_value(r),
                "in_full": True,
                "scam_type": r["top_scam_type"],
                "people": r["distinct_reporters"],
                "cities": towns,
                "first_seen": fmt(r["first_seen"]),
                "last_seen": fmt(r["last_seen"]),
            }
        )
    return {"days": KNOWN_DAYS, "total": len(items), "scams": items[:KNOWN_LIMIT]}
