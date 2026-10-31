"""Demo data: a handful of memorable numbers, one per story, so a live demo can look them up.

    uv run python -m judge.demo_seed --base-url https://scammap-huii.onrender.com

Resets the server, plays each story, then looks every number up and prints what the app says.
"""

from __future__ import annotations

import argparse
import random
import sys
from collections.abc import Callable
from typing import Any

import httpx

from judge.catalog import Ctx, area_reports
from judge.sms_scripts import SCRIPTS, fill
from judge.world import GRUDGE_NOTES

Story = tuple[str, str, str, str, Callable[[Ctx, str], list[dict[str, Any]]], Callable[[dict[str, Any]], bool]]


# Written by hand so no two are near copies (the copy check would rightly merge those).
NOTES = [
    "Caller said he was from SBI fraud team and my card would be blocked, asked for the OTP",
    "Got a call about KYC update pending, he wanted me to install anydesk to fix it",
    "बैंक से बोल रहा हूं कहकर ओटीपी मांगा, मैंने दे दिया और पैसे कट गए",
    "Fake customer care, told me to share screen for refund and took 12000 from my account",
    "Said my electricity would be cut tonight unless I paid a fine through a link he sent",
    "Asked for card number and CVV saying it was for reward points redemption",
]


def victims(n: int, st: str = "otp-call", t: str = "phone") -> Callable[[Ctx, str], list[dict[str, Any]]]:
    def play(x: Ctx, v: str) -> list[dict[str, Any]]:
        return [x.rep(value=v, st=st, t=t, note=NOTES[i], hours_ago=6 + 9 * i, shot=i % 2 == 0, lost=[0, 4999, 12000][i % 3])
                for i in range(n)]  # fmt: skip
    return play


def one_person_six_times(x: Ctx, v: str) -> list[dict[str, Any]]:
    who = x.g.person()
    return [x.victim(v, who=who, hours_ago=10 + 24 * i) for i in range(6)]


def one_wifi_22_accounts(x: Ctx, v: str) -> list[dict[str, Any]]:
    ip = x.g.isp[0]
    return [x.rep(who=(x.rid(), ip), value=v, hours_ago=x.r.uniform(0.5, 8), lag_min=x.r.uniform(1, 20)) for _ in range(22)]


def forty_friends_bakery(x: Ctx, v: str) -> list[dict[str, Any]]:
    ips = x.r.sample(x.g.isp, 30)
    return [x.rep(who=(x.rid(), x.r.choice(ips)), value=v, note=x.r.choice([g for g in GRUDGE_NOTES if g]),
                  st=x.r.choice(["otp-call", "fake-customer-care", "other", "lottery-prize"]),
                  hours_ago=x.r.uniform(0.5, 48), lag_min=x.r.uniform(2, 60)) for _ in range(40)]  # fmt: skip


def ten_friends_two_accounts(x: Ctx, v: str) -> list[dict[str, Any]]:
    reps = []
    for _ in range(10):
        ip, t0 = x.r.choice(x.g.isp), x.r.uniform(1, 30)
        for acct in range(2):
            reps.append(x.rep(who=(x.rid(), ip), value=v, note="This number called and asked for my OTP pretending to be from the bank",
                              hours_ago=t0, lag_min=5 + acct * x.r.uniform(1, 8)))  # fmt: skip
    return reps


def bots_instant(x: Ctx, v: str) -> list[dict[str, Any]]:
    return [x.rep(value=v, note=x.victim(v)["note"], hours_ago=x.r.uniform(0.2, 0.9), lag_min=x.r.uniform(0.1, 1)) for _ in range(25)]


def same_script(script: str, n: int, start_h: float) -> Callable[[Ctx, str], list[dict[str, Any]]]:
    """One SMS script sent from a new number each time; victims report from the pasted message."""

    def play(x: Ctx, v: str) -> list[dict[str, Any]]:
        r = random.Random(v)
        reps = []
        for i in range(n):
            body = x.victim(v, st=SCRIPTS[script][0], hours_ago=start_h + 7 * i, shot=i % 2 == 0)
            body["message"] = fill(script, r, num=v.replace(" ", ""))
            reps.append(body)
        return reps

    return play


def none(x: Ctx, v: str) -> list[dict[str, Any]]:
    return []


def verdict(want: str) -> Callable[[dict[str, Any]], bool]:
    return lambda b: b.get("verdict") == want


STORIES: list[Story] = [
    ("Real scam, 5 victims over 2 days", "phone", "98450 11111", "KNOWN_SCAM, number shown", victims(5), verdict("KNOWN_SCAM")),
    ("Real UPI scam, 4 victims", "upi", "refund.helpdesk@ybl", "KNOWN_SCAM", victims(4, "fake-customer-care", "upi"), verdict("KNOWN_SCAM")),
    ("Only 2 victims so far", "phone", "98450 22222", "SUSPICIOUS, number masked", victims(2), verdict("SUSPICIOUS")),
    ("One angry person, 6 reports", "phone", "98450 33333", "SUSPICIOUS, counted as 1", one_person_six_times, verdict("SUSPICIOUS")),
    ("22 fake accounts on one Wi-Fi", "phone", "98450 44444", "SUSPICIOUS, counted as 1", one_wifi_22_accounts, verdict("SUSPICIOUS")),
    ("40 friends attack a bakery", "phone", "98450 55555", "SUSPICIOUS, never KNOWN", forty_friends_bakery, verdict("SUSPICIOUS")),
    ("10 friends x 2 accounts, same text", "phone", "98450 66666", "SUSPICIOUS, never KNOWN", ten_friends_two_accounts, verdict("SUSPICIOUS")),
    ("25 bots within a minute", "phone", "98450 88888", "SUSPICIOUS, never KNOWN", bots_instant, verdict("SUSPICIOUS")),
    ("Owner disputes it (after 4 reports)", "phone", "98450 77777", "SUSPICIOUS, challenged", victims(4), lambda b: b.get("challenged") is True and b.get("verdict") == "SUSPICIOUS"),
    ("Real helpline, people report it anyway", "phone", "1930", "VERIFIED_BUSINESS", victims(6, "fake-customer-care"), verdict("VERIFIED_BUSINESS")),
    ("Same SMS script, number 1 of 3", "phone", "98451 10001", "KNOWN_SCAM, found by wording", same_script("electricity", 4, 70), verdict("KNOWN_SCAM")),
    ("Same SMS script, number 2 of 3", "phone", "98451 10002", "KNOWN_SCAM, found by wording", same_script("electricity", 4, 40), verdict("KNOWN_SCAM")),
    ("Same SMS script, number 3 of 3", "phone", "98451 10003", "KNOWN_SCAM, found by wording", same_script("electricity", 3, 8), verdict("KNOWN_SCAM")),
    ("Nobody reported it", "phone", "98450 99999", "NO_REPORTS", none, verdict("NO_REPORTS")),
]  # fmt: skip


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    a = ap.parse_args()
    c = httpx.Client(base_url=a.base_url, timeout=60)
    x = Ctx(c, 4242)
    x.reset()
    for _, _t, v, _, play, _ in STORIES:
        x.post(play(x, v))
    x.c.post("/challenges", json={"identifier_type": "phone", "identifier_value": "98450 77777", "claimant_name": "Sharma Sweets",
                                  "contact_email": "owner@example.com", "proof_note": "GST certificate attached."})  # fmt: skip
    # Koramangala: 2 a day for a week, then 10 today, so the area shows a spike on the map.
    x.post(area_reports(x, "560034", 2, (1.05, 8), ["otp-call"]) + area_reports(x, "560034", 10, (0.05, 0.95), ["otp-call"]))

    ok = True
    print(f"| Story | Type | Look up | Expected | App says | Counted | Shown as | OK |\n|{'---|' * 8}")
    for name, t, v, want, _, check in STORIES:
        b = x.look(v, t)
        good = check(b)
        ok &= good
        print(f"| {name} | {t} | `{v}` | {want} | {b.get('verdict')} | {b.get('distinct_reporters')} | `{b.get('display_value')}` | {'yes' if good else 'NO'} |")
    sms = fill("electricity", random.Random(1), num="7012345678")  # a fresh send nobody has reported
    found = x.c.post("/explore/similar", json={"text": sms}).json().get("matches", [])
    ok &= len(found) == 3
    print(f"\nWording search for a new send of the electricity script finds {len(found)} numbers: "
          f"{[m['display_value'] for m in found]}")  # fmt: skip
    alerts = x.alerts("560034")
    spike = [i for i in alerts if i["type"] == "SPIKE"]
    ok &= bool(spike)
    print(f"\nArea 560034 alerts: {[(i['type'], i.get('count'), i.get('baseline_per_day')) for i in alerts]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
