"""Scam map and area alerts (brief, Appendix A.4 and A.5). Locations are always area centroids."""

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.db import get_engine
from app.domain import alerts as A
from app.domain.areas import AREAS, AREAS_BY_PINCODE, Area
from app.repos import store

EARTH_RADIUS_KM = 6371.0


class UnknownArea(ValueError):
    pass


def haversine_km(a: Area, b: Area) -> float:
    lat1, lng1, lat2, lng2 = map(math.radians, (a.lat, a.lng, b.lat, b.lng))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lng2 - lng1) / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))


def _area(pincode: str) -> Area:
    area = AREAS_BY_PINCODE.get(pincode.strip())
    if area is None:
        raise UnknownArea("pincode is not a known area")
    return area


def scam_map(pincode: str, days: float, radius_km: float, now: datetime) -> dict[str, Any]:
    centre = _area(pincode)
    nearby = [a for a in AREAS if haversine_km(centre, a) <= radius_km]
    with get_engine().connect() as conn:
        rows = store.trusted_area_reports(conn, [a.pincode for a in nearby], now - timedelta(days=days))
    by_area: dict[str, Counter[str]] = defaultdict(Counter)
    for r in rows:
        if r["occurred_at"] <= now:
            by_area[r["pincode"]][r["scam_type"]] += 1
    clusters = []
    for area in sorted(nearby, key=lambda a: haversine_km(centre, a)):
        types = by_area.get(area.pincode)
        if not types:
            continue
        count = sum(types.values())
        clusters.append(
            {
                "pincode": area.pincode,
                "locality": area.locality,
                "city": area.city,
                "count": count,
                "top_scam_type": types.most_common(1)[0][0],
                "severity": A.severity(count),
                "lat": area.lat,
                "lng": area.lng,
            }
        )
    return {"clusters": clusters}


def area_alerts(pincode: str, now: datetime) -> dict[str, Any]:
    area = _area(pincode)
    with get_engine().connect() as conn:
        rows = store.trusted_area_reports(conn, [area.pincode], now - timedelta(days=8))
        seen_before = store.area_scam_types_between(
            conn, area.pincode, now - timedelta(days=31), now - timedelta(hours=24)
        )
    trusted = [
        A.TrustedReport(r["occurred_at"], r["scam_type"], r["reporter_key"], r["ip_key"]) for r in rows
    ]
    out: list[dict[str, object]] = []
    spike = A.spike(area.pincode, trusted, now)
    if spike:
        out.append(spike)
    out.extend(A.new_types(area.pincode, trusted, seen_before, now))
    return {"alerts": out}
