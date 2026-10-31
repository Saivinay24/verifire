#!/usr/bin/env python3
"""Ping the Render health endpoint every 10 minutes so the free instance never sleeps.

    nohup python3 scripts/keepalive.py &disown          # fire and forget
    python3 scripts/keepalive.py --interval 300         # custom interval (seconds)
    python3 scripts/keepalive.py --once                 # single ping, for cron

Render free-tier spins down after 15 minutes of inactivity. The spin-up takes 30-50 s,
which would blow the 0.5 s lookup latency check on judging day.
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))

URL = "https://scammap-huii.onrender.com/health"
INTERVAL = 600  # 10 minutes — well within the 15-minute sleep window


def ping(url: str) -> tuple[bool, str]:
    """Return (ok, message) for one health check."""
    import urllib.error
    import urllib.request

    try:
        t0 = time.monotonic()
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode()
            ms = (time.monotonic() - t0) * 1000
            return True, f"{resp.status} in {ms:.0f} ms — {body.strip()}"
    except urllib.error.HTTPError as e:
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=URL)
    ap.add_argument("--interval", type=int, default=INTERVAL, help="seconds between pings")
    ap.add_argument("--once", action="store_true", help="single ping then exit")
    args = ap.parse_args()

    while True:
        ok, msg = ping(args.url)
        stamp = datetime.now(IST).strftime("%Y-%m-%d %H:%M:%S IST")
        status = "✓" if ok else "✗"
        print(f"[{stamp}] {status} {msg}", flush=True)
        if args.once:
            return 0 if ok else 1
        time.sleep(args.interval)


if __name__ == "__main__":
    sys.exit(main())
