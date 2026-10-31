"""City pulse and live statistics for the app: what people near you, and across VeriFire, are reporting.

Same rules as the map and alerts. Only reports the trust engine counted (alert_weight > 0) shape
trends, so spam, fake accounts and pile-ons never make a scam look "hot". A number is shown in full
only once it is unmasked (3+ independent people), otherwise masked exactly as in a lookup. Report
times in the feed are cut to the hour. Nothing about who reported ever leaves this module.
"""

from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import RowMapping

from app.db import get_engine
from app.domain import alerts as A
from app.domain.areas import AREAS, AREAS_BY_PINCODE
from app.domain.identifiers import IdentifierType, mask
from app.domain.timefmt import IST, fmt
from app.domain.trust import Verdict
from app.repos import store
from app.services.areas import _area

KNOWN_LIMIT = 10
FEED_LIMIT = 15
SPIKE_LOOKBACK_DAYS = 8  # the spike baseline needs the 7 days before the last 24 hours
DAILY_DAYS = 14


def public_value(row: RowMapping) -> str:
    """The identifier as a lookup would show it: in full only when unmasked or verified."""
    if row["unmasked"] or row["verified"]:
        return str(row["value_norm"])
    return mask(IdentifierType(row["id_type"]), row["value_norm"])


def _trusted(row: RowMapping) -> bool:
    return bool(row["alert_weight"]) and row["alert_weight"] > 0


def _as_trusted(row: RowMapping) -> A.TrustedReport:
    return A.TrustedReport(row["occurred_at"], row["scam_type"], row["reporter_key"], row["ip_key"])


def _ranked(counter: Counter[str], key: str) -> list[dict[str, Any]]:
    total = sum(counter.values())
    return [
        {key: name, "count": n, "share": round(n / total, 3) if total else 0.0}
        for name, n in counter.most_common()
    ]


def city_pulse(pincode: str, days: float, now: datetime) -> dict[str, Any]:
    centre = _area(pincode)
    city = [a for a in AREAS if a.city == centre.city]
    since = now - timedelta(days=days)
    with get_engine().connect() as conn:
        rows = store.reports_with_identifiers(
            conn, now - timedelta(days=max(days, SPIKE_LOOKBACK_DAYS)), [a.pincode for a in city]
        )
    rows = [r for r in rows if r["occurred_at"] <= now]
    window = [r for r in rows if r["occurred_at"] >= since]
    counted = [r for r in window if _trusted(r)]

    by_area: dict[str, list[RowMapping]] = defaultdict(list)
    for r in counted:
        by_area[r["pincode"]].append(r)
    trusted_8d: dict[str, list[A.TrustedReport]] = defaultdict(list)
    for r in rows:
        if _trusted(r):
            trusted_8d[r["pincode"]].append(_as_trusted(r))

    areas = []
    for a in city:
        items = by_area.get(a.pincode)
        if not items:
            continue
        # Counted reports only, so the areas add up to the sheet's headline. Then people, not rows,
        # with one connection worth at most ~1.25 people.
        count = max(1, round(A.effective_count(_as_trusted(r) for r in items)))
        types = Counter(r["scam_type"] for r in items)
        areas.append(
            {
                "pincode": a.pincode,
                "locality": a.locality,
                "count": count,
                "top_scam_type": types.most_common(1)[0][0],
                "severity": A.severity(count),
                "spike": A.spike(a.pincode, trusted_8d[a.pincode], now) is not None,
                "lat": a.lat,
                "lng": a.lng,
            }
        )
    areas.sort(key=lambda x: (not x["spike"], -x["count"]))

    known: dict[int, dict[str, Any]] = {}
    for r in window:
        if r["verdict"] != Verdict.KNOWN_SCAM or not r["unmasked"] or r["challenged"] or r["verified"]:
            continue
        item = known.setdefault(
            r["identifier_id"],
            {
                "identifier_type": r["id_type"],
                "display_value": public_value(r),
                "scam_type": r["top_scam_type"],
                "people": r["distinct_reporters"],
                "last_seen": fmt(r["last_seen"]),
                "localities": set(),
            },
        )
        item["localities"].add(AREAS_BY_PINCODE[r["pincode"]].locality)
    known_all = sorted(known.values(), key=lambda k: -k["people"])
    for k in known_all:
        k["localities"] = sorted(k["localities"])
    known_list = known_all[:KNOWN_LIMIT]

    recent = [
        {
            "occurred_at": fmt(r["occurred_at"].astimezone(IST).replace(minute=0, second=0, microsecond=0)),
            "channel": r["channel"],
            "scam_type": r["scam_type"],
            "pincode": r["pincode"],
            "locality": AREAS_BY_PINCODE[r["pincode"]].locality,
            "identifier_type": r["id_type"],
            "display_value": public_value(r),
            "verdict": r["verdict"],
        }
        for r in counted
        if not r["verified"]
    ]

    # The chosen area on its own, so a person sees their neighbourhood before the whole city.
    here_counted = [r for r in counted if r["pincode"] == centre.pincode]
    here_area = next((x for x in areas if x["pincode"] == centre.pincode), None)
    here = {
        "pincode": centre.pincode,
        "locality": centre.locality,
        "reports": sum(r["pincode"] == centre.pincode for r in window),
        "counted": len(here_counted),
        "people": here_area["count"] if here_area else 0,
        "spike": bool(here_area and here_area["spike"]),
        "scam_types": _ranked(Counter(r["scam_type"] for r in here_counted), "scam_type"),
        "known_scams": [k for k in known_all if centre.locality in k["localities"]][:KNOWN_LIMIT],
        "recent": [x for x in recent if x["pincode"] == centre.pincode][:FEED_LIMIT],
    }
    recent = recent[:FEED_LIMIT]

    return {
        "city": centre.city,
        "pincode": centre.pincode,
        "days": days,
        "reports": len(window),
        "counted": len(counted),
        "areas": areas,
        "scam_types": _ranked(Counter(r["scam_type"] for r in counted), "scam_type"),
        "known_scams": known_list,
        "recent": recent,
        "here": here,
    }


def live_stats(days: float, now: datetime) -> dict[str, Any]:
    since = now - timedelta(days=days)
    with get_engine().connect() as conn:
        rows = store.reports_with_identifiers(conn, now - timedelta(days=max(days, DAILY_DAYS)))
    rows = [r for r in rows if r["occurred_at"] <= now]
    window = [r for r in rows if r["occurred_at"] >= since]
    counted = [r for r in window if _trusted(r)]

    today = now.astimezone(IST).date()
    dates = [today - timedelta(days=i) for i in range(DAILY_DAYS - 1, -1, -1)]
    per_day: dict[Any, list[int]] = {d: [0, 0] for d in dates}
    for r in rows:
        d = r["occurred_at"].astimezone(IST).date()
        if d in per_day:
            per_day[d][0] += 1
            per_day[d][1] += _trusted(r)
    week_ago, fortnight_ago = now - timedelta(days=7), now - timedelta(days=14)
    week = [r for r in rows if _trusted(r) and r["occurred_at"] >= week_ago]
    prev = [r for r in rows if _trusted(r) and fortnight_ago <= r["occurred_at"] < week_ago]

    return {
        "days": days,
        "reports": len(window),
        "counted": len(counted),
        "set_aside": len(window) - len(counted),
        "numbers_reported": len({r["identifier_id"] for r in window}),
        "known_scam_numbers": len(
            {r["identifier_id"] for r in window if r["verdict"] == Verdict.KNOWN_SCAM and not r["challenged"]}
        ),
        "money_lost_inr": sum(int(r["amount_lost_inr"] or 0) for r in counted),
        "this_week": len(week),
        "last_week": len(prev),
        "by_scam_type": _ranked(Counter(r["scam_type"] for r in counted), "scam_type"),
        "by_channel": _ranked(Counter(r["channel"] for r in counted), "channel"),
        "by_city": _ranked(Counter(AREAS_BY_PINCODE[r["pincode"]].city for r in counted), "city"),
        "daily": [{"date": d.isoformat(), "reports": per_day[d][0], "counted": per_day[d][1]} for d in dates],
    }
