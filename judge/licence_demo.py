"""Row 5, the four-step licence demo from the brief, run against a live server and timed.

    uv run python -m judge.licence_demo --base-url https://scammap-huii.onrender.com

1. With a long licence the server works and GET /license says who and until when.
2. Upload a licence that expires in 5 minutes; everything still works.
3. After it expires, every address except /health and /license answers 403 LICENSE_EXPIRED.
4. Upload a new licence: the server works again at once, no restart, and the data is still there.

Needs the private key (~/.scammap-keys), so it runs on the vendor laptop only. It finishes by
restoring the long licence, so the server is left exactly as it was found.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from scripts.mint_licence import DEFAULT_KEY, mint

LOCKED = [
    ("get", "/lookup", {"type": "phone", "value": "9876543210"}),
    ("get", "/map", {"pincode": "560102"}),
    ("get", "/alerts", {"pincode": "560102"}),
    ("post", "/reports", {}),
    ("post", "/challenges", {}),
    ("post", "/admin/reset", None),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--minutes", type=float, default=5)
    ap.add_argument("--out", type=Path, default=Path("evidence"))
    a = ap.parse_args()
    log: list[str] = [
        f"# Licence demo, {datetime.now().isoformat(timespec='seconds')}",
        "",
        f"Target: {a.base_url}",
        "",
    ]
    ok = True

    def step(cond: bool, text: str) -> None:
        nonlocal ok
        ok &= cond
        log.append(f"- {'PASS' if cond else 'FAIL'} {text}")
        print(log[-1], flush=True)

    with httpx.Client(base_url=a.base_url, timeout=30) as c:
        long_doc = mint("Demo Bank", timedelta(days=365), DEFAULT_KEY)
        r = c.post("/license", json=long_doc)
        info = c.get("/license").json()
        step(
            r.status_code == 200 and info.get("status") == "valid",
            f"1. long licence active: {json.dumps(info)}",
        )
        # A report filed now must still be there after the licence lapses (lock, never delete).
        probe = "9" + str(int(time.time()))[-9:]
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        filed = c.post("/reports", json={
            "report_id": f"rep_licdemo_{probe}", "occurred_at": now, "reported_at": now, "reporter_id": "r_licdemo",
            "ip_prefix": "10.20.30", "channel": "Phone call", "scam_type": "otp-call", "identifier_type": "phone",
            "identifier_value": probe, "pincode": "560102", "note": "asked for OTP pretending to be the bank",
            "has_screenshot": False, "amount_lost_inr": 0})  # fmt: skip
        before = c.get("/lookup", params={"type": "phone", "value": probe})
        report_count = before.json().get("report_count")
        step(
            filed.status_code == 201 and report_count == 1,
            f"1. report filed and found: {filed.status_code}, count {report_count}",
        )

        short = mint("Demo Bank (5 min)", timedelta(minutes=a.minutes), DEFAULT_KEY)
        r = c.post("/license", json=short)
        step(r.status_code == 200, f"2. short licence uploaded: {r.text[:160]}")
        step(c.get("/map", params={"pincode": "560102"}).status_code == 200, "2. still working before expiry")

        expires = datetime.fromisoformat(short["expires_at"])
        wait = (expires - datetime.now(expires.tzinfo)).total_seconds() + 15
        print(f"waiting {wait:.0f}s for expiry at {short['expires_at']}", flush=True)
        time.sleep(max(0, wait))

        t0 = time.perf_counter()
        for method, path, params in LOCKED:
            resp: Any = c.get(path, params=params) if method == "get" else c.post(path, json=params)
            body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
            step(
                resp.status_code == 403 and body.get("error") == "LICENSE_EXPIRED",
                f"3. {method.upper()} {path} -> {resp.status_code} {body}",
            )
        h = c.get("/health")
        step(h.status_code == 200 and h.json() == {"ok": True}, f"3. /health still answers: {h.text}")
        lic = c.get("/license").json()
        step(lic.get("status") == "expired", f"3. GET /license says expired: {lic}")
        log.append(f"  (refusals observed {time.perf_counter() - t0:.1f}s after the check began)")

        r = c.post("/license", json=mint("Demo Bank", timedelta(days=365), DEFAULT_KEY))
        step(r.status_code == 200, "4. new licence uploaded")
        after = c.get("/lookup", params={"type": "phone", "value": probe})
        step(after.status_code == 200, f"4. works again at once, no restart: {after.status_code}")
        step(
            after.json().get("report_count") == report_count,
            f"4. data kept: report_count {report_count} -> {after.json().get('report_count')}",
        )

    log += ["", f"**{'ALL FOUR STEPS PASS' if ok else 'FAILED'}**"]
    a.out.mkdir(parents=True, exist_ok=True)
    (a.out / f"licence_demo_{datetime.now().strftime('%Y%m%d-%H%M')}.md").write_text("\n".join(log) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
