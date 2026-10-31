"""Disputes: the owner of a number asks for a review (brief, Appendix A.7, bonus).

The brief's rule: after a dispute, a lookup shows "challenged": true and is never KNOWN_SCAM while
under review. Taken alone that rule is a shield: a scammer could dispute every number he uses and
turn each red "reported as a scam" into an amber "be careful" for good. So every dispute has a
lifecycle, and each way out is decided by something a scammer does not control:

  under_review --> upheld     a reviewer agrees: reports received so far are set aside
               --> rejected   a reviewer disagrees: the normal verdict returns
               --> overruled  new victims keep reporting it (see reports.overruled)
               --> lapsed     nobody decided within DISPUTE_REVIEW_WINDOW: the normal verdict returns

Rejected, overruled and lapsed numbers cannot be disputed again for DISPUTE_LOCK. While a dispute
is open the evidence stays visible (how many people, what scam, when), so people are still warned;
only the strongest label waits for the review. Reviewer endpoints sit behind REVIEW_KEY and never
show who reported anything.
"""

import time
import uuid
from datetime import datetime
from typing import Any

from app.db import get_engine
from app.domain import constants as C
from app.domain.catalog import verified_owner
from app.domain.identifiers import mask, normalise, parse_type
from app.domain.timefmt import fmt
from app.repos import store
from app.services.reports import keyed_hash, recompute

UNDER_REVIEW = "under_review"
DECISIONS = {"upheld", "rejected"}
CLOSED_LOCKING = {"rejected", "overruled", "lapsed"}


class AlreadyReviewed(Exception):
    """This number's last dispute ended against the claim recently: HTTP 409."""

    def __init__(self, status: str) -> None:
        super().__init__(status)
        self.status = status


class TooMany(Exception):
    """Too many disputes from one network in a day: HTTP 429."""


class NotFound(Exception):
    """No such dispute, or it cannot take that decision: HTTP 404 / 400."""


def _optional(payload: dict[str, Any], name: str, limit: int) -> str | None:
    value = payload.get(name)
    return value.strip()[:limit] if isinstance(value, str) and value.strip() else None


def challenge(payload: dict[str, Any], network: str) -> dict[str, str]:
    id_type = parse_type(str(payload.get("identifier_type") or ""))
    value = normalise(id_type, str(payload.get("identifier_value") or ""))
    email = _optional(payload, "contact_email", 200)
    ip_key = keyed_hash("dispute-ip", network)
    with get_engine().begin() as conn:
        ident = store.lock_identifier(conn, id_type, value, verified_owner(id_type, value) is not None)
        # Settle first: an expired dispute must not block or be returned as if still open.
        recompute(conn, ident["id"], verified=ident["verified"])
        existing = store.open_challenge(conn, ident["id"])
        if existing is not None:  # One open dispute per identifier.
            return {"challenge_id": existing["id"], "status": existing["status"]}
        last = store.last_closed_challenge(conn, ident["id"])
        if (
            last is not None
            and last["status"] in CLOSED_LOCKING
            and last["decided_at"] is not None
            and store.db_now(conn) - last["decided_at"] < C.DISPUTE_LOCK
        ):
            raise AlreadyReviewed(last["status"])
        if (
            store.count_network_challenges(conn, ip_key, C.DISPUTE_NETWORK_WINDOW)
            >= C.DISPUTE_PER_NETWORK_DAY
        ):
            raise TooMany
        challenge_id = "chl_" + uuid.uuid4().hex[:12]
        store.insert_challenge(
            conn,
            {
                "id": challenge_id,
                "identifier_id": ident["id"],
                "status": UNDER_REVIEW,
                "claimant_name": _optional(payload, "claimant_name", 200),
                "contact_email": email,
                "proof_note": _optional(payload, "proof_note", 2000),
                "ip_key": ip_key,
                "claimant_key": keyed_hash("dispute-contact", email.lower()) if email else None,
            },
            C.DISPUTE_REVIEW_WINDOW,
        )
        recompute(conn, ident["id"], verified=ident["verified"])
    return {"challenge_id": challenge_id, "status": UNDER_REVIEW}


def decide(challenge_id: str, decision: str) -> dict[str, str]:
    """A reviewer's decision. Upheld also works on an overruled or lapsed dispute (a late review)."""
    if decision not in DECISIONS:
        raise NotFound("decision must be upheld or rejected")
    with get_engine().begin() as conn:
        row = store.get_challenge(conn, challenge_id)
        if row is None:
            raise NotFound("no such dispute")
        if row["status"] == "upheld" or (decision == "rejected" and row["status"] != UNDER_REVIEW):
            raise NotFound(f"this dispute is already {row['status']}")
        ident = store.identifier_by_id(conn, row["identifier_id"])
        store.lock_identifier(conn, ident["id_type"], ident["value_norm"], ident["verified"])
        store.close_challenge(conn, challenge_id, decision)
        if decision == "upheld":
            store.clear_reports_before(conn, ident["id"])
        recompute(conn, ident["id"], verified=ident["verified"])
    return {"challenge_id": challenge_id, "status": decision}


_last_sweep = 0.0
SWEEP_EVERY_SECONDS = 60.0


def sweep(force: bool = False) -> int:
    """Close disputes past their deadline. Cheap and throttled; called before public reads."""
    global _last_sweep
    if not force and time.monotonic() - _last_sweep < SWEEP_EVERY_SECONDS:
        return 0
    _last_sweep = time.monotonic()
    with get_engine().connect() as conn:
        due = store.due_challenges(conn)
    for identifier_id in due:
        with get_engine().begin() as conn:
            ident = store.identifier_by_id(conn, identifier_id)
            store.lock_identifier(conn, ident["id_type"], ident["value_norm"], ident["verified"])
            recompute(conn, identifier_id, verified=ident["verified"])
    return len(due)


def review_queue(status: str) -> dict[str, Any]:
    """What a reviewer needs to decide, and nothing about who reported."""
    statuses = [UNDER_REVIEW] if status == "open" else ["upheld", "rejected", "overruled", "lapsed"]
    with get_engine().connect() as conn:
        rows = store.review_queue(conn, statuses)
        by_contact = store.claimant_counts(conn, "claimant_key")
        by_network = store.claimant_counts(conn, "ip_key")
        now = store.db_now(conn)
        items = []
        for r in rows:
            money, losses, areas = store.report_money(conn, r["identifier_id"], None)
            explain = r["explain"] or {}
            items.append(
                {
                    "challenge_id": r["id"],
                    "status": r["status"],
                    "opened": fmt(r["created_at"]),
                    "closes": fmt(r["closes_at"]),
                    "decided": fmt(r["decided_at"]),
                    "hours_left": _hours(r["closes_at"], now) if r["status"] == UNDER_REVIEW else None,
                    "identifier_type": r["id_type"],
                    "identifier_value": r["value_norm"],
                    "shown_publicly_as": mask(parse_type(r["id_type"]), r["value_norm"]),
                    "claimant_name": r["claimant_name"],
                    "contact_email": r["contact_email"],
                    "proof_note": r["proof_note"],
                    "same_contact_disputes": by_contact.get(r["claimant_key"], 1)
                    if r["claimant_key"]
                    else None,
                    "same_network_disputes": by_network.get(r["ip_key"], 1) if r["ip_key"] else None,
                    "evidence": {
                        "verdict_now": r["verdict"],
                        "reports": r["report_count"],
                        "people": r["distinct_reporters"],
                        "described": explain.get("described_groups"),
                        "pile_on": explain.get("pile_on"),
                        "score": explain.get("score"),
                        "scam_type": r["top_scam_type"],
                        "first_seen": fmt(r["first_seen"]),
                        "last_seen": fmt(r["last_seen"]),
                        "money_lost_inr": money,
                        "reports_with_loss": losses,
                        "areas": areas,
                    },
                }
            )
    return {"disputes": items}


def _hours(closes: datetime | None, now: datetime) -> float | None:
    return None if closes is None else round(max(0.0, (closes - now).total_seconds() / 3600), 1)
