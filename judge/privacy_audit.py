"""Privacy audit: the brief's privacy rules checked at every layer, not just in API replies.

    uv run python -m judge.privacy_audit --base-url http://127.0.0.1:8811 --log <server log> --seeds 9001 9002

Brief: disqualified if "a reporter can be identified, exact locations are stored, personal data is
scraped". Plus: numbers with fewer than 3 reporters hidden, evidence never shows who / IP / note,
the map never shows a person's location, careful wording.

Layers checked after loading full judge worlds:
  1. Database: every column of every table, scanned for any raw reporter_id, IP prefix or note text.
  2. Keyed hashes: stored reporter / IP keys are not a plain (unkeyed) hash anyone could recompute.
  3. Server logs: scanned for reporter ids, IP prefixes, notes and identifier values.
  4. Every API reply (lookup in every spelling, map for every area and radius, alerts, city sheet,
     live stats, report replies, errors, licence, areas): scanned for the same, and masking checked under 3 people,
     including one person reporting many times and 22 accounts on one Wi-Fi.
  5. Error replies never echo the input back.
  6. The app: never sends coordinates to the server, and has no accusing words in either language.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import sqlalchemy as sa

from judge.world import AREAS, IST, build

ACCUSING_EN = ["fraud", "fraudster", "criminal", "scammer", "this person", "cheat", "thief", "guilty"]
ACCUSING_HI = ["धोखेबाज़", "धोखेबाज", "अपराधी", "ठग है", "चोर"]


class Audit:
    def __init__(self) -> None:
        self.rows: dict[str, list[int]] = defaultdict(lambda: [0, 0])
        self.fails: list[str] = []

    def check(self, name: str, ok: bool, why: str = "") -> None:
        self.rows[name][1] += 1
        self.rows[name][0] += ok
        if not ok:
            self.fails.append(f"{name}: {why}")


def secrets_of(reports: list[dict[str, Any]]) -> tuple[set[str], set[str], set[str]]:
    rids = {r["reporter_id"] for r in reports}
    ips = {r["ip_prefix"] for r in reports}
    notes = {r["note"] for r in reports if len(r["note"]) >= 20}
    return rids, ips, notes


def leaks(text: str, rids: set[str], ips: set[str], notes: set[str]) -> list[str]:
    found = [s for s in rids if s in text] + [s for s in ips if re.search(rf"(?<![\d.]){re.escape(s)}(?![\d])", text)]
    return found + [n[:30] for n in notes if n in text or n[:40] in text]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--log", type=Path, required=True)
    ap.add_argument("--seeds", type=int, nargs="+", default=[9001, 9002])
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    au = Audit()
    engine = sa.create_engine(os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1))
    log_start = a.log.stat().st_size if a.log.exists() else 0
    c = httpx.Client(base_url=a.base_url, timeout=60)
    all_reports: list[dict[str, Any]] = []

    for seed in a.seeds:
        w = build(seed)
        c.post("/admin/reset")
        replies: list[str] = []
        for rep in w.reports:
            r = c.post("/reports", json=rep)
            replies.append(r.text)
        all_reports += w.reports
        rids, ips, notes = secrets_of(w.reports)

        # ---- 1 and 2: the database itself
        with engine.connect() as conn:
            for table in ("identifiers", "reports", "challenges", "licence_state", "areas"):
                dump = json.dumps([dict(r) for r in conn.execute(sa.text(f"SELECT * FROM {table}")).mappings()], default=str)
                found = leaks(dump, rids, ips, notes)
                au.check("1. database holds no reporter id, IP prefix or note text", not found, f"seed {seed} table {table}: {found[:3]}")
            cols = {r[0] for r in conn.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'reports'"))}
            au.check("1. reports table has no location or free-text column", not (cols & {"lat", "lng", "latitude", "longitude", "note", "note_text", "ip", "reporter_id"}), str(sorted(cols)))
            keys = conn.execute(sa.text("SELECT reporter_key, ip_key FROM reports LIMIT 200")).all()
            plain = {hashlib.sha256(x.encode()).hexdigest() for x in rids | ips} | {hashlib.md5(x.encode()).hexdigest() for x in rids | ips}
            au.check("2. stored keys are keyed hashes, not recomputable plain hashes", not any(k in plain for row in keys for k in row), "plain hash found")

        # ---- 4: every API reply
        for text in replies:
            found = leaks(text, rids, ips, notes)
            au.check("4. report replies leak nothing", not found, str(found[:3]))
        by_val: dict[tuple[str, str], set[str]] = defaultdict(set)
        hidden: set[str] = set()  # full values the lookup kept masked; the city sheet must too
        for e in w.expects:
            for v in e.variants or [e.raw]:
                body = c.get("/lookup", params={"type": e.id_type, "value": v})
                text = body.text
                found = leaks(text, rids, ips, notes)
                au.check("4. lookup replies leak nothing", not found, f"{e.scenario}: {found[:3]}")
                if body.status_code != 200:
                    continue
                b = body.json()
                by_val[(e.id_type, e.canonical)].add(b["display_value"])
                for item in b.get("evidence", []):
                    au.check("4. evidence has only time, channel, type, area", set(item) <= {"occurred_at", "channel", "scam_type", "pincode"}, str(sorted(item)))
                if b["distinct_reporters"] < 3 and e.kind != "verified" and e.canonical:
                    full = e.canonical[3:] if e.id_type == "phone" else e.canonical.lower().removeprefix("https://")
                    au.check(f"4. hidden under 3 people ({e.kind})", full not in text.lower(), f"{e.scenario} {e.canonical} shown as {b['display_value']}")
                    hidden.add(full)
                if e.kind == "attack" and e.canonical:
                    full = e.canonical[3:] if e.id_type == "phone" else e.canonical.lower().removeprefix("https://")
                    au.check("4. attacked numbers are never unmasked (spam, fake accounts, friends)", full not in text.lower(),
                             f"{e.scenario} report_count={b['report_count']} distinct={b['distinct_reporters']} shown {b['display_value']}")
                    hidden.add(full)
                low = json.dumps(b, ensure_ascii=False).lower()
                au.check("4. no accusing words in lookup replies", not [x for x in ACCUSING_EN if x in low], b.get("summary", ""))
        for pin in AREAS:
            for radius in (2, 25, 3000):
                text = c.get("/map", params={"pincode": pin, "radius_km": radius}).text
                au.check("4. map replies leak nothing", not leaks(text, rids, ips, notes))
                for cl in json.loads(text)["clusters"]:
                    _, _, la, lo = AREAS[cl["pincode"]]
                    au.check("4. every map point is an official area point", (cl["lat"], cl["lng"]) == (la, lo), str(cl))
            text = c.get("/alerts", params={"pincode": pin}).text
            au.check("4. alert replies leak nothing", not leaks(text, rids, ips, notes))
        feed_keys = {"occurred_at", "channel", "scam_type", "pincode", "locality", "identifier_type", "display_value", "verdict"}
        for pin in AREAS:
            for days in (1, 7, 90):
                text = c.get("/city", params={"pincode": pin, "days": days}).text
                low = text.lower()
                au.check("4. city sheet replies leak nothing", not leaks(text, rids, ips, notes))
                shown = sorted(h for h in hidden if h and h in low)
                au.check("4. city sheet never shows a number the lookup keeps hidden", not shown, f"{pin}: {shown[:3]}")
                b = json.loads(text)
                for item in b["recent"]:
                    au.check("4. city feed has only time, channel, type, area, masked value", set(item) <= feed_keys, str(sorted(item)))
                    au.check("4. city feed times are rounded to the hour", item["occurred_at"][14:19] == "00:00", item["occurred_at"])
                for ar in b["areas"]:
                    _, _, la, lo = AREAS[ar["pincode"]]
                    au.check("4. every city sheet point is an official area point", (ar["lat"], ar["lng"]) == (la, lo), str(ar))
                au.check("4. no accusing words in city sheet replies", not [x for x in ACCUSING_EN if x in low])
        for days in (1, 30, 365):
            text = c.get("/stats", params={"days": days}).text
            au.check("4. stats replies leak nothing", not leaks(text, rids, ips, notes))
            au.check("4. stats never name a number", not [h for h in hidden if h and h in text.lower()])
        for path in ("/license", "/health", "/ready", "/areas"):
            au.check("4. other replies leak nothing", not leaks(c.get(path).text, rids, ips, notes), path)

    # ---- 5: errors never echo input back
    probe = "SECRET-PROBE-7f3a"
    base = dict(all_reports[0], report_id="probe1", reporter_id=probe)
    for patch in ({"identifier_value": probe}, {"pincode": probe}, {"occurred_at": probe}, {"identifier_type": probe}):
        r = c.post("/reports", json={**base, **patch})
        au.check("5. error replies never echo the input", probe not in r.text, f"{patch} -> {r.text[:120]}")
    for t, v in (("phone", probe), (probe, "9876543210"), ("upi", probe)):
        r = c.get("/lookup", params={"type": t, "value": v})
        au.check("5. error replies never echo the input", probe not in r.text, f"{t}={v} -> {r.text[:120]}")
    r = c.get("/map", params={"pincode": probe})
    au.check("5. error replies never echo the input", probe not in r.text, r.text[:120])

    # ---- 3: server logs
    c.close()
    if a.log.exists():
        log = a.log.read_bytes()[log_start:].decode(errors="replace")
        rids, ips, notes = secrets_of(all_reports)
        values = {r["identifier_value"].strip() for r in all_reports if len(r["identifier_value"].strip()) >= 6}
        found = leaks(log, rids, ips, notes) + [v for v in values if v in log] + ([probe] if probe in log else [])
        au.check("3. server logs hold no reporter id, IP, note or reported identifier", not found, f"{len(found)} found, e.g. {found[:3]}")
        au.check("3. server logs were actually written during the audit", log.count('"msg": "request"') + log.count('"request"') > 100,
                 f"{len(log)} bytes")  # fmt: skip

    # ---- 6: the app itself
    static = Path(__file__).parent.parent / "app/static"
    js = "\n".join((static / f).read_text() for f in ("app.js", "ids.js"))
    sends = re.findall(r'api\(\s*"/reports"[^;]*', js) + re.findall(r"JSON\.stringify\(([^)]*)\)", js)
    au.check("6. app never sends coordinates (only the area code)", not any(k in " ".join(sends) for k in ("latitude", "longitude", "coords", "la,", "lo,")), str(sends)[:200])
    geo = js[js.find("getCurrentPosition"): js.find("getCurrentPosition") + 900]
    au.check("6. 'near me' picks the nearest area on the phone itself", "AREAS.forEach" in geo and "fetch(" not in geo, geo[:160])
    strings = " ".join(re.findall(r'"([^"]{3,})"', js) + re.findall(r"`([^`]{3,})`", js)).lower()
    bad = [w for w in ACCUSING_EN + ACCUSING_HI if w.lower() in strings]
    au.check("6. no accusing words anywhere in the app (English and Hindi)", not bad, str(bad))
    au.check("6. no login, accounts or tracking in the app", not re.search(r"password|login|signin|analytics|gtag|facebook", js, re.I), "")

    total_ok = all(p == n for p, n in au.rows.values())
    lines = [f"# Privacy audit, {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}", "",
             f"Target: `{a.base_url}`, seeds {a.seeds} ({len(all_reports)} reports loaded), database and server log inspected directly.", "",
             "| Check | Passed |", "|---|---|"]  # fmt: skip
    lines += [f"| {'✅' if p == n else '❌'} {name} | {p}/{n} |" for name, (p, n) in sorted(au.rows.items())]
    lines += ["", f"**{'ALL PRIVACY CHECKS PASS' if total_ok else 'PRIVACY FAILURES FOUND'}**", ""]
    lines += ["## Failures", ""] + ([f"- {f}" for f in au.fails[:60]] or ["None."])
    a.out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:4 + len(au.rows) + 3]))
    print(f"{len(au.fails)} failures")
    return 0 if total_ok else 1


if __name__ == "__main__":
    sys.exit(main())
