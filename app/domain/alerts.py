"""Area alerts (brief, Appendix A.5) computed on trust-filtered reports only.

Only reports the trust rules counted reach this module (first report of each independent group,
on identifiers whose campaign shape looks real). On top of that, within a window one reporter
counts once and one internet connection adds at most ~1.25 people, so a sybil farm spread over
many fake numbers in one area still cannot fake a spike (bonus: fakes never alert).
"""

import math
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.domain import constants as C


@dataclass(frozen=True)
class TrustedReport:
    occurred_at: datetime
    scam_type: str
    reporter_key: str
    ip_key: str


def effective_count(items: Iterable[TrustedReport]) -> float:
    per_reporter: dict[str, str] = {}
    for r in items:
        per_reporter.setdefault(r.reporter_key, r.ip_key)
    per_ip: dict[str, int] = defaultdict(int)
    for ip in per_reporter.values():
        per_ip[ip] += 1
    return sum(
        n if n == 1 else min(n, 1.0 + C.IP_CAP_SLOPE * math.log(n), C.IP_CAP_MAX) for n in per_ip.values()
    )


def poisson_tail(k: int, mu: float) -> float:
    """P(X >= k) for X ~ Poisson(mu): how surprising today's count is against the baseline."""
    if k <= 0:
        return 1.0
    term = math.exp(-mu)
    cdf = term
    for i in range(1, k):
        term *= mu / i
        cdf += term
    return max(0.0, 1.0 - cdf)


def spike(pincode: str, reports: list[TrustedReport], now: datetime) -> dict[str, object] | None:
    last_day = [r for r in reports if now - timedelta(hours=24) <= r.occurred_at <= now]
    before = [r for r in reports if now - timedelta(days=8) <= r.occurred_at < now - timedelta(hours=24)]
    count = effective_count(last_day)
    baseline = effective_count(before) / 7
    if count < C.SPIKE_MIN_COUNT or count < C.SPIKE_RATIO * baseline:
        return None
    shown = round(count)
    return {
        "type": "SPIKE",
        "pincode": pincode,
        "window": "24h",
        "count": shown,
        "baseline_per_day": round(baseline, 2),
        "p_value": round(poisson_tail(shown, max(baseline, 1.0)), 5),
    }


def new_types(
    pincode: str, reports: list[TrustedReport], seen_before: set[str], now: datetime
) -> list[dict[str, object]]:
    recent = sorted(
        {r.scam_type for r in reports if now - timedelta(hours=24) <= r.occurred_at <= now} - seen_before
    )
    return [{"type": "NEW_TYPE", "pincode": pincode, "scam_type": t, "window": "24h"} for t in recent]


def severity(count: int) -> str:
    if count >= 10:
        return "CRIT"
    if count >= 5:
        return "HIGH"
    return "MED"
