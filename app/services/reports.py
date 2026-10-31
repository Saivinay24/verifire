"""Report ingest and the per-identifier trust recompute.

Each new report locks its identifier row, is stored in privacy-safe form, and triggers a recompute
of that identifier only (O(its reports)). The verdict is cached on the identifier row so a lookup
is a single indexed read.
"""

import hashlib
import hmac
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import Connection, RowMapping
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.db import get_engine
from app.domain import constants as C
from app.domain import trust
from app.domain.areas import AREAS_BY_PINCODE
from app.domain.catalog import canonical_channel, canonical_scam_type, verified_owner
from app.domain.identifiers import IdentifierType, InvalidIdentifier, normalise, parse_type
from app.domain.notes import extract
from app.domain.timefmt import InvalidTime, fmt, parse
from app.repos import store

MAX_CLOCK_SKEW = timedelta(minutes=5)


class ReportRejected(ValueError):
    """Invalid report: HTTP 400 with this message."""


class RateLimited(Exception):
    """Reporter is being slowed down: HTTP 429 (brief, rule 4)."""


@dataclass(frozen=True)
class Accepted:
    report_id: str
    case_id: str
    merged: bool


def keyed_hash(kind: str, value: str) -> str:
    """HMAC-SHA256 with a server secret: stable for linking, useless for identifying (privacy rule 1)."""
    secret = get_settings().reporter_hmac_secret.encode()
    return hmac.new(secret, f"{kind}:{value}".encode(), hashlib.sha256).hexdigest()


def case_id(identifier_id: int) -> str:
    return f"case_{identifier_id}"


def _ip_block(raw: str) -> str:
    """The /24 a reporter came from. A full address is cut to its first three parts."""
    parts = raw.strip().split(".")
    return ".".join(parts[:3])


def _text(payload: dict[str, Any], name: str, required: bool = True) -> str:
    value = payload.get(name)
    if value is None or (isinstance(value, str) and not value.strip()):
        if required:
            raise ReportRejected(f"{name} is required")
        return ""
    if not isinstance(value, str):
        raise ReportRejected(f"{name} must be text")
    return value.strip()


def validate(payload: dict[str, Any], now: datetime) -> dict[str, Any]:
    """Check and normalise a raw report. Raises ReportRejected for anything the brief says is a 400."""
    report_id = _text(payload, "report_id")
    try:
        id_type = parse_type(_text(payload, "identifier_type"))
        value_norm = normalise(id_type, _text(payload, "identifier_value"))
    except InvalidIdentifier as exc:
        raise ReportRejected(f"identifier: {exc}") from exc
    try:
        occurred_at = parse(payload.get("occurred_at"))
        reported_raw = payload.get("reported_at")
        reported_at = parse(reported_raw) if reported_raw else occurred_at
    except InvalidTime as exc:
        raise ReportRejected(str(exc)) from exc
    if occurred_at > now + MAX_CLOCK_SKEW:
        raise ReportRejected("occurred_at is in the future")
    if reported_at < occurred_at:
        raise ReportRejected("reported_at is before occurred_at")
    pincode = _text(payload, "pincode")
    if pincode not in AREAS_BY_PINCODE:
        raise ReportRejected("pincode is not a known area")
    reporter_id = _text(payload, "reporter_id")
    ip_prefix = _text(payload, "ip_prefix")
    note = payload.get("note")
    if note is not None and not isinstance(note, str):
        raise ReportRejected("note must be text")
    amount = payload.get("amount_lost_inr") or 0
    if isinstance(amount, bool) or not isinstance(amount, int | float) or amount < 0:
        raise ReportRejected("amount_lost_inr must be a number of rupees")
    features = extract((note or "")[:2000])
    return {
        "report_id": report_id,
        "id_type": id_type,
        "value_norm": value_norm,
        "row": {
            "report_id": report_id,
            "reporter_key": keyed_hash("reporter", reporter_id),
            "ip_key": keyed_hash("ip", _ip_block(ip_prefix)),
            "occurred_at": occurred_at,
            "reported_at": reported_at,
            "channel": canonical_channel(payload.get("channel")),
            "scam_type": canonical_scam_type(payload.get("scam_type")),
            "pincode": pincode,
            "note_len": features.length,
            "note_sig": features.signature,
            "note_lex": features.mentions_method,
            "note_scam": features.names_scam,
            "note_review": features.is_review,
            "has_screenshot": payload.get("has_screenshot") is True,
            "amount_lost_inr": int(amount),
        },
    }


def submit(payload: dict[str, Any], now: datetime) -> Accepted:
    report = validate(payload, now)
    row = report["row"]
    try:
        with get_engine().begin() as conn:
            existing = store.find_report(conn, report["report_id"])
            if existing is not None:  # The same report sent twice is stored once.
                return Accepted(report["report_id"], case_id(existing["identifier_id"]), True)
            id_type: IdentifierType = report["id_type"]
            ident = store.lock_identifier(
                conn, id_type, report["value_norm"], verified_owner(id_type, report["value_norm"]) is not None
            )
            since = row["reported_at"] - C.RATE_WINDOW
            same = store.count_reporter_reports(
                conn, row["reporter_key"], since, row["reported_at"], identifier_id=ident["id"]
            )
            if same >= C.RATE_SAME_IDENTIFIER:
                raise RateLimited
            if store.count_reporter_reports(conn, row["reporter_key"], since, row["reported_at"]) >= (
                C.RATE_PER_REPORTER
            ):
                raise RateLimited
            merged = store.count_identifier_reports(conn, ident["id"]) > 0
            store.insert_report(conn, {**row, "identifier_id": ident["id"]})
            recompute(conn, ident["id"], verified=ident["verified"])
            return Accepted(report["report_id"], case_id(ident["id"]), merged)
    except IntegrityError:
        # Two copies of one report raced; the first one won. Answer like a duplicate.
        with get_engine().connect() as conn:
            existing = store.find_report(conn, report["report_id"])
        if existing is None:
            raise
        return Accepted(report["report_id"], case_id(existing["identifier_id"]), True)


def _facts(
    rows: Sequence[RowMapping], hourly: dict[str, int], flagged: set[str], verified: bool
) -> list[trust.ReportFacts]:
    return [
        trust.ReportFacts(
            id=str(r["id"]),
            reporter_key=r["reporter_key"],
            ip_key=r["ip_key"],
            occurred_at=r["occurred_at"],
            reported_at=r["reported_at"],
            pincode=r["pincode"],
            scam_type=r["scam_type"],
            note_len=r["note_len"],
            note_sig=r["note_sig"],
            note_lex=r["note_lex"],
            note_scam=r["note_scam"],
            note_review=r["note_review"],
            has_screenshot=r["has_screenshot"],
            amount_lost_inr=r["amount_lost_inr"],
            reporter_hourly=hourly.get(r["reporter_key"], 1),
            # Reporting a verified number counts against a reporter only on *other* identifiers.
            reporter_flagged=(r["reporter_key"] in flagged) and not verified,
        )
        for r in rows
    ]


def overruled(dispute: RowMapping, rows: Sequence[RowMapping], facts: Sequence[trust.ReportFacts]) -> bool:
    """New victims overrule a dispute: people and networks not seen before it, reporting after it,
    who on their own clear the full KNOWN_SCAM bar, spread over DISPUTE_OVERRULE_SPREAD.

    Times are the server's receive times, which no client can set. Reports from anyone who had
    already reported the number before the dispute never count: they are the original accusers.
    """
    opened = dispute["created_at"]
    seen_people = {r["reporter_key"] for r in rows if r["received_at"] <= opened}
    seen_networks = {r["ip_key"] for r in rows if r["received_at"] <= opened}
    after = [
        i
        for i, r in enumerate(rows)
        if r["received_at"] > opened
        and r["reporter_key"] not in seen_people
        and r["ip_key"] not in seen_networks
    ]
    if not after:
        return False
    fresh = trust.evaluate([facts[i] for i in after])
    if not trust.established(fresh, C.KNOWN_MIN_SCORE):
        return False
    counted = [rows[i]["received_at"] for i in after if facts[i].id in fresh.alert_ids]
    return len(counted) >= 2 and max(counted) - min(counted) >= C.DISPUTE_OVERRULE_SPREAD


def recompute(conn: Connection, identifier_id: int, *, verified: bool) -> trust.Verdict:
    """Re-score one identifier and settle its open dispute, if any (lapsed or overruled)."""
    ident = store.identifier_by_id(conn, identifier_id)
    every = store.identifier_reports(conn, identifier_id)
    cleared = ident["cleared_before"]
    # An upheld review sets aside everything received up to the decision; the number starts fresh.
    rows = [r for r in every if cleared is None or r["received_at"] > cleared]
    hourly = store.reporter_hourly_counts(conn, identifier_id)
    flagged = store.reporters_of_verified(conn, {r["reporter_key"] for r in rows})
    facts = _facts(rows, hourly, flagged, verified)
    result = trust.evaluate(facts)

    dispute = store.open_challenge(conn, identifier_id)
    challenged = False
    # The dispute's public state rides in `explain`, so a lookup needs no extra query.
    state = (ident["explain"] or {}).get("dispute")
    if dispute is not None:
        if store.db_now(conn) >= dispute["closes_at"]:
            store.close_challenge(conn, dispute["id"], "lapsed")
            state = {"status": "lapsed"}
        elif overruled(dispute, rows, facts):
            store.close_challenge(conn, dispute["id"], "overruled")
            state = {"status": "overruled"}
        else:
            challenged = True
            state = {"status": "under_review", "closes_at": fmt(dispute["closes_at"])}
    elif state and state.get("status") == "under_review":  # Just decided by a reviewer.
        last = store.last_closed_challenge(conn, identifier_id)
        state = {"status": last["status"]} if last is not None else None
    verdict = trust.decide(verified=verified, challenged=challenged, report_count=len(rows), result=result)

    changes = []
    for r in every:
        group = result.group_of.get(str(r["id"]))
        weight = (
            0 if verified else int(str(r["id"]) in result.alert_ids)
        )  # Set-aside rows: not in result, so 0.
        if r["group_key"] != group or r["alert_weight"] != weight:
            changes.append({"rid": r["id"], "g": group, "w": weight})
    store.update_report_trust(conn, changes)

    types = Counter(r["scam_type"] for r in rows)
    store.update_identifier(
        conn,
        identifier_id,
        {
            "verdict": verdict.value,
            "report_count": len(rows),
            "distinct_reporters": result.groups,
            "trust_score": result.score,
            "campaign_factor": result.campaign_factor,
            "unmasked": trust.can_unmask(verified=verified, result=result),
            "first_seen": min((r["occurred_at"] for r in rows), default=None),
            "last_seen": max((r["occurred_at"] for r in rows), default=None),
            "top_scam_type": types.most_common(1)[0][0] if types else None,
            "challenged": challenged,
            "explain": {**result.explain, "dispute": state} if state else result.explain,
        },
    )
    return verdict
