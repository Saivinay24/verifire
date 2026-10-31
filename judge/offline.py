"""Fast, in-memory trust check: judge worlds straight through the trust rules, no HTTP or database.

    uv run python -m judge.offline --seeds 9101-9110 9201-9210

Approximates the server (no per-reporter hourly velocity, no verified-reporter flag), so it is for
iterating on trust rules. The live judge run (judge.run) stays the source of truth.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from app.domain import trust
from app.domain.notes import extract
from judge.world import IST, Expect, build


def facts(i: int, rep: dict[str, Any]) -> trust.ReportFacts:
    f = extract(rep["note"])
    return trust.ReportFacts(
        id=str(i), reporter_key=rep["reporter_id"], ip_key=rep["ip_prefix"],
        occurred_at=datetime.fromisoformat(rep["occurred_at"]), reported_at=datetime.fromisoformat(rep["reported_at"]),
        pincode=rep["pincode"], scam_type=rep["scam_type"], note_len=f.length, note_sig=f.signature,
        note_lex=f.mentions_method, note_scam=f.names_scam, note_review=f.is_review,
        has_screenshot=rep["has_screenshot"], amount_lost_inr=rep["amount_lost_inr"],
    )  # fmt: skip


def verdict(reps: list[dict[str, Any]]) -> tuple[trust.Verdict, trust.TrustResult]:
    res = trust.evaluate([facts(i, r) for i, r in enumerate(reps)])
    return trust.decide(verified=False, challenged=False, report_count=len(reps), result=res), res


def self_poisoning(seed: int) -> list[str]:
    """4 real victims make a number Known scam; then the scammer floods 15 blank reports onto it."""
    from judge.world import Gen

    now = datetime.now(IST)
    g = Gen(seed, now)
    t, _, _, var = g.ident(("phone",))
    st = "otp-call"
    reps = []
    for _ in range(4):
        note = ""
        while not note:
            note = g.victim_note(st)
        reps.append(g.report(who=g.person(), id_type=t, value=var[0], pincode="560102", scam_type=st,
                             occurred=g.ago(30, 200), lag=g.lag(), note=note))  # fmt: skip
    before, _ = verdict(reps)
    for _ in range(15):
        who = ("r_" + "".join(g.r.choices("0123456789abcdef", k=8)), g.r.choice(g.isp))
        reps.append(g.report(who=who, id_type=t, value=var[0], pincode="560102", scam_type=g.r.choice(["other", st]),
                             occurred=g.ago(0.5, 3), lag=timedelta(minutes=2), note=""))  # fmt: skip
    after, res = verdict(reps)
    if before is not trust.Verdict.KNOWN_SCAM:
        return [f"seed {seed} self-poisoning: 4 victims alone were {before}"]
    if after is not trust.Verdict.KNOWN_SCAM:
        return [f"seed {seed} self-poisoning: demoted to {after} by 15 blank reports, pile_on={res.pile_on}"]
    return []


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", nargs="+", default=["9101-9110", "9201-9210"])
    a = ap.parse_args()
    seeds = [
        s
        for spec in a.seeds
        for s in (range(int(spec.split("-")[0]), int(spec.split("-")[1]) + 1) if "-" in spec else [int(spec)])
    ]

    tally: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    fails: list[str] = []
    for seed in seeds:
        w = build(seed)
        by_value: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
        for r in w.reports:
            by_value[(r["identifier_type"], r["identifier_value"])].append(r)
        for e in w.expects:
            if e.kind not in ("genuine-known", "attack", "low-report"):
                continue
            reps = [r for v in set(e.variants) for r in by_value.get((e.id_type, v), [])]
            v, res = verdict(reps)
            name, ok = check(e, v, res)
            tally[name][1] += 1
            tally[name][0] += ok
            if not ok:
                fails.append(f"seed {seed} {e.scenario} {e.canonical}: {v} groups={res.groups} described={res.described_groups} "
                             f"score={res.score} pile_on={res.pile_on} merged={res.explain.get('merged_by')}")  # fmt: skip
        sp = self_poisoning(seed)
        tally["self-poisoning stays KNOWN"][1] += 1
        tally["self-poisoning stays KNOWN"][0] += not sp
        fails += sp

    for name, (p, n) in sorted(tally.items()):
        print(f"{'PASS' if p == n else 'FAIL'}  {name:<40} {p}/{n}")
    print(f"\n{len(fails)} failures")
    for f in fails:
        print(" -", f)
    return 1 if fails else 0


def check(e: Expect, v: trust.Verdict, res: trust.TrustResult) -> tuple[str, bool]:
    if e.kind == "attack":
        return f"trick never KNOWN: {e.scenario.split('-')[0]}", v is not trust.Verdict.KNOWN_SCAM
    if e.kind == "low-report":
        return "1-2 reporters SUSPICIOUS", v is trust.Verdict.SUSPICIOUS
    bucket = "k3-4" if e.reporters <= 4 else "k5-9" if e.reporters <= 9 else "k10+"
    return f"genuine {bucket} KNOWN and counted 3+", v is trust.Verdict.KNOWN_SCAM and res.groups >= 3


if __name__ == "__main__":
    sys.exit(main())
