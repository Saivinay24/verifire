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


# ---------------- The rest of the world: enough for every screen to have something real ----------------
# Each city gets the scam mix it is known for, so the map, city sheets, stats and Explore all differ.
CITY_TYPES = {
    "Bengaluru": ["otp-call", "fake-kyc-link", "courier-customs", "job-offer", "investment-group",
                  "fake-customer-care", "electricity-disconnection", "upi-refund-qr"],
    "Mumbai": ["courier-customs", "digital-arrest", "investment-group", "fake-kyc-link"],
    "Delhi": ["digital-arrest", "loan-app-harassment", "otp-call", "lottery-prize"],
    "Hyderabad": ["investment-group", "job-offer", "upi-refund-qr"],
    "Chennai": ["fake-kyc-link", "electricity-disconnection", "otp-call"],
    "Pune": ["job-offer", "investment-group", "fake-customer-care"],
    "Kolkata": ["lottery-prize", "otp-call", "loan-app-harassment"],
    "Ahmedabad": ["investment-group", "upi-refund-qr", "courier-customs"],
    "Jaipur": ["fake-kyc-link", "lottery-prize", "electricity-disconnection"],
    "Lucknow": ["loan-app-harassment", "otp-call", "digital-arrest"],
    "Kochi": ["job-offer", "courier-customs", "fake-customer-care"],
}  # fmt: skip
SCENE_AREAS = {"560034", "560038"}  # the spike and new-type stories keep their own exact pattern


def background(x: Ctx) -> list[dict[str, Any]]:
    """Two weeks of everyday single reports in every area, at different intensities."""
    from judge.world import AREAS as WA

    reps = []
    for pin, (_, city, _, _) in WA.items():
        if pin in SCENE_AREAS or city not in CITY_TYPES:
            continue
        per_day = (1.1 if city == "Bengaluru" else 1.8) * x.r.uniform(0.35, 1.7)
        for _ in range(round(per_day * 14)):
            t, raw, _, _ = x.g.ident(("phone", "phone", "phone", "phone", "upi", "url"))
            reps.append(x.rep(t=t, value=raw, pin=pin, st=x.r.choice(CITY_TYPES[city]), hours_ago=x.r.uniform(1, 14 * 24),
                              lost=x.r.choice([0, 0, 0, 0, 1500, 4999, 25000])))  # fmt: skip
    return reps


# (value, type, scam type, pincode, victims, SMS script or None). Some scripts run on two numbers in
# two cities, so Explore's wording search links them.
CAMPAIGNS = [
    ("98201 40001", "phone", "courier-customs", "400050", 5, "parcel"),
    ("99101 40002", "phone", "courier-customs", "110016", 4, "parcel"),
    ("99102 50001", "phone", "digital-arrest", "110016", 5, "arrest"),
    ("94150 50002", "phone", "digital-arrest", "226010", 3, "arrest"),
    ("profit.desk22@axl", "upi", "investment-group", "500081", 4, None),
    ("90110 60001", "phone", "job-offer", "411014", 4, "job"),
    ("94470 60002", "phone", "job-offer", "682030", 3, "job"),
    ("98300 70001", "phone", "lottery-prize", "700091", 4, "lottery"),
    ("https://sbi-kyc-verify24.in/update", "url", "fake-kyc-link", "302017", 4, "kyc"),
    ("https://kyc-update-now.in/login", "url", "fake-kyc-link", "600020", 3, "kyc"),
    ("VM-KYCUPD", "sender_id", "fake-kyc-link", "560066", 3, "kyc"),
    ("refund.cell@ybl", "upi", "upi-refund-qr", "380015", 4, None),
]


def campaign(x: Ctx, value: str, t: str, st: str, pin: str, n: int, script: str | None) -> list[dict[str, Any]]:
    r = random.Random(value)
    reps = []
    for i in range(n):
        body = x.victim(value, st=st, t=t, pin=pin, hours_ago=4 + 19 * i + r.uniform(0, 6), shot=i % 2 == 0,
                        lost=[0, 9500, 0, 48000, 0][i % 5])  # fmt: skip
        if script:
            num = value.replace(" ", "") if t == "phone" else None
            text = fill(script, r, num=num)
            body["message"] = text if t == "phone" else f"{text} {value}"
        reps.append(body)
    return reps


# A loan app's numbers, all disputed by one contact: the review page's bulk-dispute case.
LOAN_APP = ["94151 80001", "94151 80002", "94151 80003"]


def play_world(x: Ctx) -> None:
    x.post(background(x))
    for value, t, st, pin, n, script in CAMPAIGNS:
        x.post(campaign(x, value, t, st, pin, n, script))
    for v in LOAN_APP:
        x.post(campaign(x, v, "phone", "loan-app-harassment", "226010", 4, None))
        x.c.post("/challenges", json={"identifier_type": "phone", "identifier_value": v, "claimant_name": "QuickCash Finance",
                                      "contact_email": "legal@quickcash.example", "proof_note": "We are a registered lender."})  # fmt: skip
    # Indiranagar: a month of OTP and KYC calls, then the first sextortion report in 3 hours: NEW_TYPE.
    x.post([*area_reports(x, "560038", 0.5, (1.05, 29), ["otp-call", "fake-kyc-link"]),
            x.victim(x.phone(), st="sextortion", pin="560038", hours_ago=3)])  # fmt: skip


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
    play_world(x)

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
    for value, t, *_ in CAMPAIGNS:
        b = x.look(value, t)
        ok &= b.get("verdict") == "KNOWN_SCAM"
        print(f"| Campaign | {t} | `{value}` | KNOWN_SCAM | {b.get('verdict')} | {b.get('distinct_reporters')} | `{b.get('display_value')}` | {'yes' if b.get('verdict') == 'KNOWN_SCAM' else 'NO'} |")  # fmt: skip
    for v in LOAN_APP:
        b = x.look(v)
        good = b.get("challenged") is True
        ok &= good
        print(f"| Loan app, disputed | phone | `{v}` | SUSPICIOUS, challenged | {b.get('verdict')} | {b.get('distinct_reporters')} | `{b.get('display_value')}` | {'yes' if good else 'NO'} |")  # fmt: skip
    for script, want in (("parcel", 2), ("arrest", 2), ("job", 2), ("kyc", 3), ("lottery", 1)):
        got = len(x.c.post("/explore/similar", json={"text": fill(script, random.Random(9))}).json().get("matches", []))
        ok &= got == want
        print(f"Wording search, new {script} send: {got} numbers (want {want})")
    known = x.c.get("/explore/known").json()
    stats = x.c.get("/stats", params={"days": 14}).json()
    days_with = sum(d["reports"] > 0 for d in stats["daily"])
    ok &= known["total"] >= 12 and days_with >= 13 and len(stats["by_city"]) == 11
    print(f"Confirmed scams: {known['total']}, stats: {stats['reports']} reports in 14 days, {stats['counted']} counted, "
          f"{days_with}/14 days with reports, {len(stats['by_city'])} cities")  # fmt: skip
    new = [i for i in x.alerts("560038") if i["type"] == "NEW_TYPE"]
    ok &= bool(new)
    print(f"Indiranagar alerts: {[(i['type'], i.get('scam_type')) for i in x.alerts('560038')]}")
    alerts = x.alerts("560034")
    spike = [i for i in alerts if i["type"] == "SPIKE"]
    ok &= bool(spike)
    print(f"\nArea 560034 alerts: {[(i['type'], i.get('count'), i.get('baseline_per_day')) for i in alerts]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
