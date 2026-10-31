"""Judge simulator: load a PRD-only world into a server and grade it row by row.

    uv run python -m judge.run --base-url https://scammap-huii.onrender.com --seeds 9001 9002 9003

Every check names the rubric row and PRD clause it comes from. A row reads PASS only when every
check in it passed on every seed. Raw failures are listed in full, never summarised away.
Nothing here imports `app`: the server is a black box, exactly as on judging day.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

from judge.world import AREAS, IST, JUNK_LOOKUPS, World, build

ROWS = {
    "1": "Stops fake reports (20)",
    "2": "Lookup gives the right answer (15)",
    "3": "Map and alerts (10)",
    "4": "Privacy (15)",
    "5": "Server and licence (15, automatable part)",
    "B": "Bonus (7)",
}
VERDICTS = {"KNOWN_SCAM", "SUSPICIOUS", "NO_REPORTS", "VERIFIED_BUSINESS"}
# Words a judge would mark down on a result screen ("This person is a fraud" loses up to 5 points).
ACCUSING = ["fraud", "fraudster", "criminal", "scammer", "this person", "cheat", "thief", "guilty"]


@dataclass
class Check:
    row: str
    name: str
    clause: str
    passed: int = 0
    total: int = 0
    failures: list[str] = field(default_factory=list)

    def record(self, ok: bool, why: str = "") -> None:
        self.total += 1
        if ok:
            self.passed += 1
        else:
            self.failures.append(why)


class Grader:
    def __init__(self) -> None:
        self.checks: dict[str, Check] = {}
        self.latencies: list[float] = []
        self.server_ms: list[float] = []
        self.info: list[str] = []

    def check(self, row: str, name: str, clause: str) -> Check:
        if name not in self.checks:
            self.checks[name] = Check(row, name, clause)
        return self.checks[name]


def km(a: tuple[float, float], b: tuple[float, float]) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def masked_ok(id_type: str, canon: str, body: dict[str, Any]) -> bool:
    """Under 3 reporters the full value must not appear anywhere in the reply."""
    text = json.dumps(body, ensure_ascii=False).lower()
    if id_type == "phone":
        return canon[3:] not in text  # the 10 digits, in any surrounding format
    if id_type == "url":
        return canon.removeprefix("https://").lower() not in text
    return canon.lower() not in text


def run_world(c: httpx.Client, w: World, gr: Grader, workers: int) -> None:
    secrets = {rep["reporter_id"] for rep in w.reports} | {rep["ip_prefix"] for rep in w.reports}
    notes = {rep["note"] for rep in w.reports if len(rep["note"]) >= 25}
    bodies: list[tuple[str, dict[str, Any]]] = []  # every reply, for the leak scan

    def get(path: str, **params: Any) -> httpx.Response:
        t0 = time.perf_counter()
        resp = c.get(path, params=params)
        if path == "/lookup":
            gr.latencies.append(time.perf_counter() - t0)
            st = resp.headers.get("server-timing", "")
            if "dur=" in st:
                gr.server_ms.append(float(st.split("dur=")[1].split(";")[0]))
        if resp.headers.get("content-type", "").startswith("application/json"):
            bodies.append((f"{path}?{params}", resp.json()))
        return resp

    r = c.post("/admin/reset")
    gr.check("5", "reset works", "A6: Delete every report and reply 200").record(
        r.status_code == 200, str(r.status_code)
    )
    if r.status_code != 200:
        return

    # ---- load, concurrently, roughly in reported_at order like a replaying tool
    statuses: dict[int, int] = defaultdict(int)
    by_id: dict[str, httpx.Response] = {}

    def post(rep: dict[str, Any]) -> tuple[str, httpx.Response]:
        return rep["report_id"], c.post("/reports", json=rep)

    t0 = time.perf_counter()
    with ThreadPoolExecutor(workers) as pool:
        for rid, resp in pool.map(post, w.reports):
            statuses[resp.status_code] += 1
            by_id[rid] = resp
            if resp.status_code == 201:
                bodies.append(("/reports", resp.json()))
    gr.info.append(
        f"seed {w.seed}: {len(w.reports)} reports in {time.perf_counter() - t0:.1f}s, statuses {dict(statuses)}"
    )
    ck = gr.check("2", "valid reports accepted", "A2: 201 with report_id, case_id, merged (429 allowed)")
    for rep in w.reports:
        resp = by_id[rep["report_id"]]
        ok = resp.status_code in (201, 429) and (
            resp.status_code == 429 or {"report_id", "case_id", "merged"} <= set(resp.json())
        )
        ck.record(
            ok,
            f"{rep['report_id']} {rep['identifier_type']}={rep['identifier_value']!r} -> {resp.status_code} {resp.text[:120]}",
        )

    # ---- junk reports
    base = dict(w.reports[0], report_id="")
    junk = [
        ("identifier 12345", {"identifier_type": "phone", "identifier_value": "12345"}),
        ("identifier abc", {"identifier_type": "phone", "identifier_value": "abc"}),
        ("bad upi", {"identifier_type": "upi", "identifier_value": "nope"}),
        ("pincode ABCDEF", {"pincode": "ABCDEF"}),
        ("pincode 12", {"pincode": "12"}),
        ("time 'yesterday'", {"occurred_at": "yesterday"}),
        ("time month 13", {"occurred_at": "2026-13-45T10:00:00+05:30"}),
        ("bad identifier_type", {"identifier_type": "email", "identifier_value": "a@b.com"}),
    ]
    ck = gr.check("1", "junk reports rejected 400", "A2: 400 when identifier, area code or time is not valid")
    for i, (label, patch) in enumerate(junk):
        resp = c.post("/reports", json={**base, **patch, "report_id": f"junk_{w.seed}_{i}"})
        ck.record(resp.status_code == 400, f"{label} -> {resp.status_code}")
    resp = c.post(
        "/reports",
        json={k: v for k, v in base.items() if k != "identifier_value"} | {"report_id": f"junk_{w.seed}_m"},
    )
    ck.record(resp.status_code == 400, f"missing identifier_value -> {resp.status_code}")

    # ---- challenge (bonus) before lookups
    for ch in w.challenges:
        resp = c.post("/challenges", json=ch)
        ok = (
            resp.status_code == 201
            and resp.json().get("status") == "under_review"
            and resp.json().get("challenge_id")
        )
        gr.check("B", "challenge accepted", "A7: 201 with challenge_id, status under_review").record(
            bool(ok), f"{resp.status_code} {resp.text[:120]}"
        )

    # ---- lookups
    for e in w.expects:
        resp = get("/lookup", type=e.id_type, value=e.raw)
        if resp.status_code != 200:
            gr.check("2", "lookup returns 200 for valid values", "A3").record(
                False, f"{e.scenario} {e.id_type}={e.raw!r} -> {resp.status_code}"
            )
            continue
        gr.check("2", "lookup returns 200 for valid values", "A3").record(True)
        b = resp.json()
        v = b.get("verdict")
        dr = b.get("distinct_reporters")
        tag = f"{e.scenario} {e.id_type}={e.canonical or e.raw} verdict={v} distinct={dr} count={b.get('report_count')}"

        shape = v in VERDICTS and all(
            k in b
            for k in (
                "verdict",
                "report_count",
                "distinct_reporters",
                "display_value",
                "evidence",
                "challenged",
            )
        )
        gr.check("2", "reply shape and verdict enum", "A3: fields and verdict is exactly one of four").record(
            shape, tag + f" keys={sorted(b)}"
        )

        ev_bad = [
            k
            for item in b.get("evidence", [])
            for k in item
            if any(s in k.lower() for s in ("reporter", "ip", "note"))
        ]
        gr.check(
            "4",
            "evidence never shows reporter, IP or note",
            "A3: evidence never includes who reported, their IP or their note",
        ).record(not ev_bad, tag + f" {ev_bad}")

        if isinstance(dr, int) and dr < 3 and e.kind != "verified":
            gr.check(
                "4", "under 3 reporters: value hidden", "A3: hide it until at least 3 different people"
            ).record(masked_ok(e.id_type, e.canonical, b), tag + f" display={b.get('display_value')!r}")

        strings = " ".join(str(x) for x in b.values() if isinstance(x, str)).lower()
        bad_words = [wd for wd in ACCUSING if wd in strings]
        gr.check("4", "no accusing words in lookup reply", "Row 4: careful wording").record(
            not bad_words, tag + f" {bad_words}"
        )

        if e.kind == "genuine-known":
            bucket = "k3-4" if e.reporters <= 4 else "k5-9" if e.reporters <= 9 else "k10+"
            gr.check(
                "2", f"real scam is KNOWN_SCAM ({bucket})", "Row 2: real scams come back Known scam"
            ).record(v == "KNOWN_SCAM", tag)
            gr.check(
                "4", "3+ real reporters: counted as 3+", "A3: distinct_reporters counts different people"
            ).record(isinstance(dr, int) and dr >= 3, tag)
        elif e.kind == "low-report":
            gr.check("2", "1-2 reporters is SUSPICIOUS", "A3: reported but not established").record(
                v == "SUSPICIOUS", tag
            )
        elif e.kind == "unreported":
            gr.check("2", "unreported is NO_REPORTS", "A3: nobody reported is 200 with NO_REPORTS").record(
                v == "NO_REPORTS" and b.get("report_count") == 0, tag
            )
        elif e.kind == "attack":
            gr.check(
                "1",
                f"trick never KNOWN_SCAM: {e.scenario.split('-')[0]}",
                "Row 1: none of these makes a number Known scam",
            ).record(v != "KNOWN_SCAM", tag + f" [{e.attack_detail}]")
            if e.scenario.startswith("spam"):
                gr.check(
                    "1", "one person N times counts as 1", "A3: One person reporting six times is 1"
                ).record(dr == 1, tag)
            if e.scenario.startswith("sybil"):
                gr.info.append(f"seed {w.seed} {e.scenario}: distinct_reporters={dr} after trust rules")
        elif e.kind == "verified":
            gr.check(
                "B", "verified entries say VERIFIED_BUSINESS", "C: must say VERIFIED_BUSINESS, never a scam"
            ).record(v == "VERIFIED_BUSINESS", tag)
        elif e.kind == "challenged":
            gr.check(
                "B", "challenged: flag set and never KNOWN", "A7: challenged true, never KNOWN_SCAM"
            ).record(b.get("challenged") is True and v != "KNOWN_SCAM", tag)

        # Every way of typing it gives the same answer.
        if e.variants and e.kind != "verified":
            key = (v, b.get("report_count"), dr)
            ck = gr.check(
                "2", "every format gives the same answer", "A rule 3: one identifier, many ways of typing it"
            )
            for var in e.variants:
                vb = get("/lookup", type=e.id_type, value=var)
                got = (
                    (
                        vb.json().get("verdict"),
                        vb.json().get("report_count"),
                        vb.json().get("distinct_reporters"),
                    )
                    if vb.status_code == 200
                    else vb.status_code
                )
                ck.record(got == key, f"{e.scenario} {var!r} -> {got} vs {key}")

    # Brief's own examples.
    for t, a, bb in [("phone", "+91 98765 43210", "09876543210"), ("phone", "98765-43210", "919876543210"),
                     ("upi", "Ravi12@OKAXIS", "ravi12@okaxis"), ("url", "http://www.sbi-kyc.in/pay?utm=sms", "https://sbi-kyc.in/pay"),
                     ("sender_id", "VM-HDFCBK", "AD-HDFCBK")]:  # fmt: skip
        ra, rb = get("/lookup", type=t, value=a), get("/lookup", type=t, value=bb)
        same = (
            ra.status_code == rb.status_code == 200
            and ra.json().get("display_value") == rb.json().get("display_value")
            and ra.json().get("verdict") == rb.json().get("verdict")
        )
        gr.check("2", "brief's format examples match", "A rule 3 examples").record(
            same, f"{a!r} vs {bb!r}: {ra.text[:90]} | {rb.text[:90]}"
        )

    ck = gr.check("2", "impossible values are 400", "A3: a value that cannot be valid, like 12345, is 400")
    for t, val in JUNK_LOOKUPS:
        resp = c.get("/lookup", params={"type": t, "value": val})
        ck.record(resp.status_code == 400, f"{t}={val!r} -> {resp.status_code}")

    # ---- map
    # The clock moves between loading and asking, so a report within 2 hours of the 7-day edge may
    # land either side. "sure" areas must be listed; "maybe" areas may be listed; nothing else.
    sure: set[str] = set()
    maybe: set[str] = set()
    in_30: set[str] = set()
    for rep in w.reports:
        if by_id[rep["report_id"]].status_code != 201:
            continue
        age_d = (datetime.now(IST) - datetime.fromisoformat(rep["occurred_at"])).total_seconds() / 86400
        if age_d <= 7 - 2 / 24:
            sure.add(rep["pincode"])
        if age_d <= 7 + 2 / 24:
            maybe.add(rep["pincode"])
        if age_d <= 30:
            in_30.add(rep["pincode"])

    ck_pt = gr.check(
        "4", "map uses only Appendix B points", "A4: use the area's map point, never a reporter's location"
    )
    ck_set = gr.check(
        "3",
        "map lists exactly the areas in radius with reports",
        "A4: one cluster per area within the radius that has reports in the window",
    )
    ck_sev = gr.check("3", "cluster fields and severity", "A4: count, top_scam_type, severity CRIT/HIGH/MED")
    for pin, (_, _, lat, lng) in AREAS.items():
        for radius in (2, 10):
            resp = get("/map", pincode=pin, radius_km=radius)
            if resp.status_code != 200:
                ck_set.record(False, f"/map {pin} r={radius} -> {resp.status_code}")
                continue
            clusters = resp.json().get("clusters", [])
            for cl in clusters:
                a = AREAS.get(cl.get("pincode", ""))
                ck_pt.record(a is not None and (cl.get("lat"), cl.get("lng")) == (a[2], a[3]), f"{cl}")
                ck_sev.record(
                    cl.get("severity") in {"CRIT", "HIGH", "MED"}
                    and isinstance(cl.get("count"), int)
                    and cl.get("count", 0) > 0
                    and bool(cl.get("top_scam_type")),
                    f"{cl}",
                )
            near = {p for p, (_, _, la, lo) in AREAS.items() if km((lat, lng), (la, lo)) <= radius}
            got = {cl.get("pincode") for cl in clusters}
            must, may = near & sure, near & maybe
            ck_set.record(
                must <= got <= may,
                f"/map {pin} r={radius}: missing {sorted(must - got)} extra {sorted(got - may)}",
            )

    old = w.areas["old"]
    resp = get("/map", pincode=old)
    gr.check("3", "month-old reports not on the map", "Row 3: month-old reports are not on the map").record(
        old not in {cl.get("pincode") for cl in resp.json().get("clusters", [])}, f"{old} {resp.text[:200]}"
    )
    resp = get("/map", pincode=old, days=30)
    gr.check("3", "days parameter widens the window", "A4: days parameter").record(
        (old in {cl.get("pincode") for cl in resp.json().get("clusters", [])}) == (old in in_30),
        f"{old} days=30 {resp.text[:200]}",
    )

    # ---- alerts
    def alerts(pin: str) -> list[dict[str, Any]]:
        resp = get("/alerts", pincode=pin)
        return (
            resp.json().get("alerts", [])
            if resp.status_code == 200
            else [{"type": f"HTTP {resp.status_code}"}]
        )

    sp = alerts(w.areas["spike"])
    gr.check(
        "3", "spike area gets SPIKE", "A5: last 24h >= 2x the daily average of the 7 days before, and >= 5"
    ).record(any(a.get("type") == "SPIKE" for a in sp), f"{w.areas['spike']} {sp}")
    nm = alerts(w.areas["normal"])
    gr.check("3", "normal area gets no SPIKE", "Row 3: a normal area does not").record(
        not any(a.get("type") == "SPIKE" for a in nm), f"{w.areas['normal']} {nm}"
    )
    nt = alerts(w.areas["new_type"])
    gr.check(
        "3", "new scam type gets NEW_TYPE", "A5: type in last 24h not seen in the 30 days before"
    ).record(
        any(a.get("type") == "NEW_TYPE" and a.get("scam_type") == w.new_type for a in nt),
        f"{w.areas['new_type']} want {w.new_type}: {nt}",
    )
    od = alerts(old)
    gr.check("3", "quiet area replies {alerts: []}", 'A5: No alerts means {"alerts": []}').record(
        od == [], f"{old} {od}"
    )

    fa = alerts(w.areas["fake_alert"])
    gr.check("B", "fake reports never set off an alert", "Bonus: fake reports never set off an alert").record(
        not any(
            a.get("type") == "SPIKE"
            or (a.get("type") == "NEW_TYPE" and a.get("scam_type") == w.fake_new_type)
            for a in fa
        ),
        f"fake_alert {w.areas['fake_alert']} (22 sybils + 6x spam of {w.fake_new_type}): {fa}",
    )
    for pin in w.attack_areas:
        aa = alerts(pin)
        gr.check("B", "fake reports never set off an alert", "Bonus").record(
            aa == [], f"attack-only area {pin}: {aa}"
        )

    # ---- privacy: nothing that identifies a reporter appears in any reply
    ck = gr.check(
        "4",
        "no reporter id, IP prefix or note in any reply",
        "Disqualification: a reporter can be identified",
    )
    for where, body in bodies:
        text = json.dumps(body, ensure_ascii=False)
        leaked = [s for s in secrets if s in text] + [n[:30] for n in notes if n in text]
        ck.record(not leaked, f"{where}: {leaked[:3]}")


def summarise(gr: Grader, seeds: list[int], base_url: str, elapsed: float) -> tuple[str, bool]:
    lines = [f"# Judge simulator run, {datetime.now(IST).isoformat(timespec='seconds')}",
             "", f"Target: {base_url}  ", f"Held-out seeds: {seeds}  ", f"Elapsed: {elapsed:.0f}s", ""]  # fmt: skip
    all_ok = True
    for row, title in ROWS.items():
        cks = [c for c in gr.checks.values() if c.row == row]
        ok = all(c.passed == c.total for c in cks)
        all_ok &= ok
        lines += [
            f"## Row {row}: {title}: {'PASS' if ok else 'FAIL'}",
            "",
            "| check | passed | PRD clause |",
            "|---|---|---|",
        ]
        lines += [f"| {c.name} | {c.passed}/{c.total} | {c.clause} |" for c in cks]
        lines.append("")
    lat = sorted(gr.latencies)
    if lat:
        p = lambda q: lat[min(len(lat) - 1, int(q * len(lat)))] * 1000  # noqa: E731
        lat_ok = p(0.95) < 500 and lat[-1] < 1.0
        all_ok &= lat_ok
        lines += [f"## Lookup latency: {'PASS' if lat_ok else 'FAIL'}", "",
                  f"{len(lat)} lookups: p50 {p(0.5):.0f} ms, p95 {p(0.95):.0f} ms, p99 {p(0.99):.0f} ms, max {lat[-1] * 1000:.0f} ms, "
                  f"mean {statistics.mean(lat) * 1000:.0f} ms (bar: under 500 ms)", ""]  # fmt: skip
        if gr.server_ms:
            sm = sorted(gr.server_ms)
            q = lambda x: sm[min(len(sm) - 1, int(x * len(sm)))]  # noqa: E731
            lines += [f"Inside the server (Server-Timing): p50 {q(0.5):.1f} ms, p95 {q(0.95):.1f} ms, "
                      f"p99 {q(0.99):.1f} ms, max {sm[-1]:.1f} ms. The rest is network between this laptop and the server.", ""]  # fmt: skip
    fails = [(c, f) for c in gr.checks.values() for f in c.failures]
    lines += [f"## Failures ({len(fails)})", ""]
    lines += [f"- [row {c.row}] {c.name}: {f}" for c, f in fails] or ["None."]
    lines += ["", "## Notes", ""] + [f"- {i}" for i in gr.info]
    lines += ["", f"**Overall: {'ALL AUTOMATABLE CHECKS PASS' if all_ok else 'NOT PASSING'}**"]
    return "\n".join(lines) + "\n", all_ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[9001, 9002, 9003])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", type=Path, default=Path("evidence"))
    a = ap.parse_args()

    gr = Grader()
    t0 = time.perf_counter()
    with httpx.Client(
        base_url=a.base_url, timeout=30, limits=httpx.Limits(max_connections=a.workers + 2)
    ) as c:
        h = c.get("/health")
        gr.check("5", "health", 'A1: 200 with {"ok": true}').record(
            h.status_code == 200 and h.json() == {"ok": True}, h.text
        )
        lic = c.get("/license")
        gr.check("5", "licence valid on this server", "Ship it: GET /license").record(
            lic.status_code == 200 and lic.json().get("status") == "valid", lic.text[:200]
        )
        gr.check("5", "served over https", "Row 5: on an https address").record(
            a.base_url.startswith("https://"), a.base_url
        )
        for seed in a.seeds:
            run_world(c, build(seed), gr, a.workers)
    text, ok = summarise(gr, a.seeds, a.base_url, time.perf_counter() - t0)
    print(text)
    a.out.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    host = a.base_url.split("//")[-1].split(":")[0].split(".")[0]
    (a.out / f"judge_{host}_{stamp}.md").write_text(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
