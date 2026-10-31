"""Trust rules: how much the reports about one identifier should count (MASTER_PLAN 4.4).

Principle: count independent voices, not reports, then ask whether those voices behave like a
real campaign. Two outputs, both explainable:

* ``groups``: independent people after linking reports that come from the same person, the same
  internet connection, the same copy-pasted text, or one lockstep burst. This is the brief's
  ``distinct_reporters`` ("one person reporting six times is 1").
* ``score``: the effective weight of those people after note quality, evidence and
  campaign-shape checks.

Pure functions only. No database, no clock, no rule that names a specific identifier.
"""

import math
import statistics
from collections import Counter, defaultdict
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum

from app.domain import constants as C
from app.domain.notes import lsh_bands, similarity


class Verdict(StrEnum):
    KNOWN_SCAM = "KNOWN_SCAM"
    SUSPICIOUS = "SUSPICIOUS"
    NO_REPORTS = "NO_REPORTS"
    VERIFIED_BUSINESS = "VERIFIED_BUSINESS"


@dataclass(frozen=True)
class ReportFacts:
    """What the trust rules may see about one report. Keys are keyed hashes, never raw values."""

    id: str
    reporter_key: str
    ip_key: str
    occurred_at: datetime
    reported_at: datetime
    pincode: str
    scam_type: str
    note_len: int
    note_sig: Sequence[int]
    note_lex: bool
    note_scam: bool
    note_review: bool
    has_screenshot: bool
    amount_lost_inr: int
    reporter_hourly: int = 1  # Max reports this reporter sent in any hour, across all identifiers.
    reporter_flagged: bool = False  # This reporter also reported a verified identifier.


@dataclass
class TrustResult:
    groups: int = 0
    described_groups: int = 0  # groups where someone said what happened (note, screenshot or loss)
    score: float = 0.0
    campaign_factor: float = 1.0
    pile_on: list[str] = field(default_factory=list)  # why this looks like a pile-on, if it does
    group_of: dict[str, str] = field(default_factory=dict)
    alert_ids: set[str] = field(default_factory=set)
    explain: dict[str, object] = field(default_factory=dict)


class _UnionFind:
    def __init__(self, items: Sequence[str]) -> None:
        self.parent = {i: i for i in items}

    def find(self, x: str) -> str:
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def union(self, a: str, b: str) -> bool:
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.parent[max(ra, rb)] = min(ra, rb)
        return True


def _near_duplicate_pairs(reports: Sequence[ReportFacts]) -> list[tuple[int, int, float]]:
    """Pairs of reports (by index) whose notes are near-copies. LSH keeps this close to linear."""
    buckets: dict[tuple[int, tuple[int, ...]], list[int]] = defaultdict(list)
    for i, r in enumerate(reports):
        for band in lsh_bands(list(r.note_sig)):
            buckets[band].append(i)
    seen: set[tuple[int, int]] = set()
    pairs = []
    for members in buckets.values():
        for x in range(len(members)):
            for y in range(x + 1, len(members)):
                pair = (members[x], members[y])
                if pair in seen:
                    continue
                seen.add(pair)
                sim = similarity(list(reports[pair[0]].note_sig), list(reports[pair[1]].note_sig))
                pairs.append((pair[0], pair[1], sim))
    return pairs


def _iqr_seconds(times: Sequence[datetime]) -> float:
    if len(times) < 4:
        return 0.0
    q = statistics.quantiles([t.timestamp() for t in times], n=4)
    return q[2] - q[0]


def evaluate(reports: Sequence[ReportFacts]) -> TrustResult:
    """Trust result for one identifier, protected against a blank flood drowning out real victims.

    A scammer can flood blank reports onto their own number to trip the "mostly blank" pile-on
    signal. So when that is the only signal, the people who wrote something are judged on their own;
    if they establish the scam by themselves, that result stands and the blank reports are set aside.
    """
    full = _evaluate(reports)
    if full.pile_on != ["mostly_blank"]:
        return full
    written = [r for r in reports if r.note_len >= C.NOTE_SHORT_CHARS]
    if not written:
        return full
    clean = _evaluate(written)
    if not _established(clean, C.KNOWN_MIN_SCORE):
        return full
    explain = {**clean.explain, "blank_set_aside": len(reports) - len(written)}
    return replace(clean, group_of=full.group_of, explain=explain)


def _evaluate(reports: Sequence[ReportFacts]) -> TrustResult:
    if not reports:
        return TrustResult(explain={"reports": 0})
    rs = sorted(reports, key=lambda r: (r.reported_at, r.id))
    ids = [r.id for r in rs]
    groups = _UnionFind(ids)
    edges: Counter[str] = Counter()

    # Step 1a: one person is one voice (spamming); one connection is one voice (fake accounts,
    # including slow-drip sybils, so the link spans the identifier's whole history).
    # Mobile carriers put many strangers behind one /24, so two accounts on a connection may be two
    # neighbours; three or more on one connection reporting the same identifier is a farm.
    accounts_on: dict[str, set[str]] = defaultdict(set)
    for r in rs:
        accounts_on[r.ip_key].add(r.reporter_key)
    # Below that, two accounts on one connection that report this identifier minutes apart are one
    # person switching accounts; neighbours on a carrier block report at unrelated times.
    last_on: dict[str, ReportFacts] = {}
    for r in rs:
        prev = last_on.get(r.ip_key)
        if (
            prev is not None
            and prev.reporter_key != r.reporter_key
            and r.reported_at - prev.reported_at <= C.SAME_CONNECTION_PAIR_WINDOW
            and groups.union(prev.id, r.id)
        ):
            edges["account_switch"] += 1
        last_on[r.ip_key] = r
    first_by: dict[tuple[str, str], str] = {}
    for r in rs:
        links = [("same_reporter", r.reporter_key)]
        if len(accounts_on[r.ip_key]) >= C.SAME_CONNECTION_MIN_ACCOUNTS:
            links.append(("same_connection", r.ip_key))
        for kind, key in links:
            anchor = first_by.setdefault((kind, key), r.id)
            if groups.union(anchor, r.id):
                edges[kind] += 1

    # Step 1b: copy-pasted notes are one voice (only notes long enough to be a description).
    dup_pairs = _near_duplicate_pairs(rs)
    note_groups = _UnionFind(ids)
    for i, j, sim in dup_pairs:
        if sim >= C.NOTE_DUP_SIMILARITY and min(rs[i].note_len, rs[j].note_len) >= C.NOTE_DUP_MIN_CHARS:
            note_groups.union(ids[i], ids[j])
            if groups.union(ids[i], ids[j]):
                edges["copied_note"] += 1

    # Step 1c: a lockstep burst (many reports in one hour, mostly blank or copied notes) is one voice.
    def note_token(r: ReportFacts) -> str:
        return "<blank>" if r.note_len < C.NOTE_SHORT_CHARS else note_groups.find(r.id)

    def coordinated(window: Sequence[ReportFacts]) -> str | None:
        """Which tell (if any) marks this burst as one actor. Needs no proof of harm plus one tell."""
        evidence = sum(r.has_screenshot or r.amount_lost_inr > 0 for r in window) / len(window)
        if evidence >= C.COORD_MAX_EVIDENCE_SHARE:
            return None
        lags = [(r.reported_at - r.occurred_at).total_seconds() for r in window]
        # A dataset where every lag is exactly 0 carries no timing information; never use it.
        if any(lags):
            quick = sum(lag < C.COORD_INSTANT_LAG.total_seconds() for lag in lags) / len(lags)
            if quick >= C.COORD_INSTANT_SHARE:
                return "instant_reporting"
        lengths = [r.note_len for r in window if r.note_len >= C.NOTE_SHORT_CHARS]
        if len(lengths) >= C.BURST_MIN_REPORTS and statistics.pstdev(lengths) / statistics.fmean(lengths) < (
            C.COORD_UNIFORM_CV
        ):
            return "uniform_text"
        top_type = Counter(r.scam_type for r in window).most_common(1)[0][1]
        if top_type / len(window) < C.COORD_SCATTER_SHARE:
            return "scattered_scam_types"
        return None

    end = 0
    for start in range(len(rs)):
        end = max(end, start)
        while end + 1 < len(rs) and rs[end + 1].reported_at - rs[start].reported_at <= C.BURST_WINDOW:
            end += 1
        window = rs[start : end + 1]
        if len(window) >= C.BURST_MIN_REPORTS:
            diversity = len({note_token(r) for r in window}) / len(window)
            tell = "lockstep_burst" if diversity < C.BURST_MIN_DIVERSITY else coordinated(window)
            if tell:
                for r in window[1:]:
                    if groups.union(window[0].id, r.id):
                        edges[tell] += 1

    group_of = {i: groups.find(i) for i in ids}
    n_groups = len(set(group_of.values()))
    described = len(
        {
            group_of[r.id]
            for r in rs
            if r.note_len >= C.NOTE_SHORT_CHARS or r.has_screenshot or r.amount_lost_inr > 0
        }
    )

    # Step 2: weight each reporter (all of one reporter's reports on this identifier = one unit).
    best_sim: dict[str, float] = defaultdict(float)
    for i, j, sim in dup_pairs:
        later = max(i, j)  # rs is time-ordered: novelty is judged against earlier notes only
        if rs[i].reporter_key != rs[j].reporter_key:
            best_sim[ids[later]] = max(best_sim[ids[later]], sim)

    units: dict[str, list[ReportFacts]] = defaultdict(list)
    for r in rs:
        units[r.reporter_key].append(r)

    def note_quality(r: ReportFacts) -> float:
        if r.note_len < C.NOTE_SHORT_CHARS:
            base = C.NOTE_WEIGHT_EMPTY
        elif r.note_len < C.NOTE_FULL_CHARS:
            base = C.NOTE_WEIGHT_SHORT
        else:
            base = 1.0
        excess = max(0.0, best_sim[r.id] - C.NOTE_NOVELTY_FREE) / (1 - C.NOTE_NOVELTY_FREE)
        novelty = max(C.NOTE_NOVELTY_FLOOR, 1.0 - C.NOTE_NOVELTY_PENALTY * excess)
        return base * novelty

    unit_weight: dict[str, float] = {}
    unit_ip: dict[str, str] = {}
    for reporter, items in units.items():
        evidence = 1.0
        evidence += C.EVIDENCE_SCREENSHOT * any(r.has_screenshot for r in items)
        evidence += C.EVIDENCE_LOSS * any(r.amount_lost_inr > 0 for r in items)
        evidence += C.EVIDENCE_LEXICON * any(r.note_lex for r in items)
        w = max(note_quality(r) for r in items) * min(C.EVIDENCE_CAP, evidence)
        w /= 1 + C.REPEAT_DAMPING * (len(items) - 1)
        hourly = max(r.reporter_hourly for r in items)
        w /= 1 + C.VELOCITY_DAMPING * max(0, hourly - C.VELOCITY_FREE_PER_HOUR)
        if any(r.reporter_flagged for r in items):
            w *= C.VERIFIED_REPORTER_FACTOR
        unit_weight[reporter] = max(C.UNIT_WEIGHT_MIN, w)
        unit_ip[reporter] = Counter(r.ip_key for r in items).most_common(1)[0][0]

    # Step 3: one internet connection can add at most ~1.25 people, however many accounts use it.
    # Each reporter keeps a proportional share of their connection's capped total; then each group
    # (one independent voice) is capped at one fully evidenced person.
    by_ip: dict[str, list[str]] = defaultdict(list)
    for reporter in unit_weight:
        by_ip[unit_ip[reporter]].append(reporter)
    scaled: dict[str, float] = {}
    for reporters in by_ip.values():
        s = sum(unit_weight[u] for u in reporters)
        n = len(reporters)
        capped = s if n == 1 else min(s, 1.0 + C.IP_CAP_SLOPE * math.log(n), C.IP_CAP_MAX)
        for u in reporters:
            scaled[u] = unit_weight[u] * capped / s
    per_group: dict[str, float] = defaultdict(float)
    for reporter, items in units.items():
        per_group[group_of[items[0].id]] += scaled[reporter]
    weight_sum = sum(min(C.GROUP_CAP, w) for w in per_group.values())

    # Step 4: campaign shape. Each factor is a mild, bounded nudge; only several together bite.
    factors: dict[str, float] = {}
    if n_groups >= C.CAMPAIGN_MIN_GROUPS:
        n_units = len(units)
        span_min = (rs[-1].reported_at - rs[0].reported_at).total_seconds() / 60
        rate = n_units / max(1.0, span_min)
        fast = rate > C.BURST_RATE_FREE
        factors["burst"] = 1 / (1 + C.BURST_RATE_DAMPING * max(0.0, rate - C.BURST_RATE_FREE))
        collapsed = n_units >= C.COORDINATION_MIN_UNITS and n_groups / n_units < C.COORDINATION_MAX_SHARE
        factors["coordination"] = C.COORDINATION_FACTOR if fast and collapsed else 1.0
        blank_share = sum(all(r.note_len < C.NOTE_SHORT_CHARS for r in it) for it in units.values()) / n_units
        mostly_blank = n_units >= C.BLANK_MIN_UNITS and blank_share > C.BLANK_MAX_SHARE
        factors["blank_notes"] = C.BLANK_FACTOR if mostly_blank else 1.0

        unit_pins = Counter(items[0].pincode for items in units.values())
        top_share = sum(c for _, c in unit_pins.most_common(C.AREA_MAX_PINCODES)) / n_units
        local_and_fast = n_units >= C.AREA_MIN_UNITS and top_share >= C.AREA_CONCENTRATION and fast
        factors["area"] = C.AREA_FACTOR if local_and_fast else 1.0

        f_img = sum(any(r.has_screenshot for r in it) for it in units.values()) / n_units
        f_loss = sum(any(r.amount_lost_inr > 0 for r in it) for it in units.values()) / n_units
        f_lex = sum(any(r.note_lex for r in it) for it in units.values()) / n_units
        evidence_frac = min(1.0, f_img + f_loss + 0.7 * f_lex)
        factors["evidence"] = C.EVIDENCE_FACTOR_BASE + C.EVIDENCE_FACTOR_SLOPE * evidence_frac

        rep_iqr = _iqr_seconds([r.reported_at for r in rs])
        occ_iqr = _iqr_seconds([r.occurred_at for r in rs])
        backdated = rep_iqr <= C.SYNC_REPORTED_IQR.total_seconds() and occ_iqr > C.SYNC_RATIO * max(
            rep_iqr, 60.0
        )
        factors["sync"] = C.SYNC_FACTOR if backdated else 1.0

        lengths = [r.note_len for r in rs if r.note_len >= C.NOTE_SHORT_CHARS]
        uniform = (
            len(lengths) >= C.STYLE_MIN_NOTES
            and statistics.pstdev(lengths) / statistics.fmean(lengths) < C.STYLE_MAX_CV
        )
        factors["style"] = C.STYLE_FACTOR if uniform else 1.0

    # Step 5: pile-on gate. Volume cannot buy a verdict: if the people behind an identifier mostly
    # wrote nothing, wrote no scam at all, or cannot agree what the scam was, it is never confirmed.
    pile_on: list[str] = []
    if len(units) >= C.PILE_ON_MIN_UNITS:
        n_units = len(units)
        noted = [it for it in units.values() if any(r.note_len >= C.NOTE_SHORT_CHARS for r in it)]
        if 1 - len(noted) / n_units >= C.PILE_ON_BLANK_SHARE:
            pile_on.append("mostly_blank")
        if (
            len(noted) >= C.PILE_ON_MIN_NOTES
            and sum(any(r.note_review for r in it) for it in noted) / len(noted) >= C.PILE_ON_REVIEW_SHARE
        ):
            pile_on.append("reviews_not_scams")
        unit_types = Counter(Counter(r.scam_type for r in it).most_common(1)[0][0] for it in units.values())
        if unit_types.most_common(1)[0][1] / n_units < C.PILE_ON_TYPE_SHARE:
            pile_on.append("no_agreement_on_type")

    campaign = min(C.CAMPAIGN_CEIL, max(C.CAMPAIGN_FLOOR, math.prod(factors.values()) if factors else 1.0))
    score = weight_sum * campaign

    alert_ids: set[str] = set()
    if campaign >= C.ALERT_MIN_CAMPAIGN and not pile_on:
        first_in_group: dict[str, ReportFacts] = {}
        group_size: Counter[str] = Counter(group_of.values())
        for r in rs:
            g = group_of[r.id]
            if g not in first_in_group or r.occurred_at < first_in_group[g].occurred_at:
                first_in_group[g] = r
        # A group that filed many reports on one identifier (spammer, fake accounts) is never news.
        alert_ids = {r.id for g, r in first_in_group.items() if group_size[g] <= C.ALERT_MAX_GROUP_REPORTS}

    return TrustResult(
        groups=n_groups,
        described_groups=described,
        score=round(score, 3),
        campaign_factor=round(campaign, 3),
        pile_on=pile_on,
        group_of=group_of,
        alert_ids=alert_ids,
        explain={
            "reports": len(rs),
            "reporters": len(units),
            "connections": len(by_ip),
            "groups": n_groups,
            "described_groups": described,
            "merged_by": dict(edges),
            "weight_after_caps": round(weight_sum, 3),
            "campaign_factors": {k: round(v, 3) for k, v in factors.items()},
            "campaign_factor": round(campaign, 3),
            "pile_on": pile_on,
            "score": round(score, 3),
        },
    )


def decide(*, verified: bool, challenged: bool, report_count: int, result: TrustResult) -> Verdict:
    if verified:
        return Verdict.VERIFIED_BUSINESS
    if report_count == 0:
        return Verdict.NO_REPORTS
    if challenged:
        return Verdict.SUSPICIOUS  # Under review: never KNOWN_SCAM, but still warn (bonus rule).
    # Real victims say what happened (brief: "in their own words"); blank clicks alone never confirm.
    if _established(result, C.KNOWN_MIN_SCORE):
        return Verdict.KNOWN_SCAM
    return Verdict.SUSPICIOUS


def _established(result: TrustResult, min_score: float) -> bool:
    """3+ independent people, 2+ of whom described it or showed harm, enough weight, not a pile-on."""
    return (
        not result.pile_on
        and result.groups >= C.KNOWN_MIN_GROUPS
        and result.described_groups >= C.KNOWN_MIN_DESCRIBED
        and result.score >= min_score
    )


def can_unmask(*, verified: bool, result: TrustResult) -> bool:
    """Privacy rule 2: show the full value only once at least 3 independent people stand behind it."""
    return verified or _established(result, C.UNMASK_MIN_SCORE)
