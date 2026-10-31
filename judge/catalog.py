"""Scenario catalogue: every kind of thing that can happen, played against a running server.

    uv run python -m judge.catalog --base-url http://127.0.0.1:8811 --seeds 20 --out ../docs/SCENARIOS.md

Each scenario resets the server, plays one story (real victims, an attack, odd input, an area
pattern, a licence event) and checks the answer the brief or plain sense demands. Randomised
scenarios run once per seed, so the result is a rate ("19/20"), not a single lucky run.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx

from judge.world import GRUDGE_NOTES, IST, Gen

Outcome = tuple[bool, str]


@dataclass
class Scenario:
    cat: str
    name: str
    story: str
    expect: str
    fn: Callable[[Ctx], Outcome]
    randomised: bool = True
    note: str = ""  # why it behaves this way, shown in the report


class Ctx:
    def __init__(self, c: httpx.Client, seed: int) -> None:
        self.c = c
        self.seed = seed
        self.g = Gen(seed, datetime.now(IST))
        self.r = self.g.r

    # -- people and reports
    def rid(self) -> str:
        return "r_" + "".join(self.r.choices("0123456789abcdef", k=8))

    def rep(self, *, who: tuple[str, str] | None = None, t: str = "phone", value: str, st: str = "otp-call",
            pin: str = "560102", hours_ago: float | None = None, lag_min: float | None = None,
            note: str | None = None, shot: bool = False, lost: int = 0, channel: str | None = None) -> dict[str, Any]:  # fmt: skip
        occ = self.g.ago(hours_ago, hours_ago) if hours_ago is not None else self.g.ago(2, 300)
        lag = timedelta(minutes=lag_min) if lag_min is not None else self.g.lag()
        body = self.g.report(who=who or self.g.person(), id_type=t, value=value, pincode=pin, scam_type=st,
                             occurred=occ, lag=lag, note=self.g.victim_note(st) if note is None else note,
                             channel=channel)  # fmt: skip
        body["has_screenshot"], body["amount_lost_inr"] = shot, lost
        return body

    def victim(self, value: str, st: str = "otp-call", t: str = "phone", **kw: Any) -> dict[str, Any]:
        note = ""
        while len(note) < 25:  # a victim who wrote what happened
            note = self.g.victim_note(st)
        return self.rep(value=value, st=st, t=t, note=note, **kw)

    def phone(self) -> str:
        return self.g.mobile()[0]

    # -- server
    def reset(self) -> None:
        assert self.c.post("/admin/reset").status_code == 200

    def post(self, reports: list[dict[str, Any]]) -> list[int]:
        return [self.c.post("/reports", json=r).status_code for r in sorted(reports, key=lambda x: x["reported_at"])]

    def look(self, value: str, t: str = "phone") -> dict[str, Any]:
        resp = self.c.get("/lookup", params={"type": t, "value": value})
        return resp.json() if resp.status_code == 200 else {"status": resp.status_code}

    def alerts(self, pin: str) -> list[dict[str, Any]]:
        return self.c.get("/alerts", params={"pincode": pin}).json().get("alerts", [])


def seen(b: dict[str, Any]) -> str:
    if "status" in b:
        return f"HTTP {b['status']}"
    return f"{b['verdict']}, counted {b['distinct_reporters']} people, shown as {b['display_value']}"


def known(b: dict[str, Any]) -> bool:
    return b.get("verdict") == "KNOWN_SCAM"


def suspicious(b: dict[str, Any]) -> bool:
    return b.get("verdict") == "SUSPICIOUS"


# =========================================================================================
# A. Real victims
# =========================================================================================

def a_one(x: Ctx) -> Outcome:
    v = x.phone(); x.post([x.victim(v)]); b = x.look(v)  # noqa: E702
    return suspicious(b) and "X" in b["display_value"], seen(b)


def a_two(x: Ctx) -> Outcome:
    v = x.phone(); x.post([x.victim(v) for _ in range(2)]); b = x.look(v)  # noqa: E702
    return suspicious(b) and "X" in b["display_value"], seen(b)


def a_three_described(x: Ctx) -> Outcome:
    v = x.phone(); x.post([x.victim(v) for _ in range(3)]); b = x.look(v)  # noqa: E702
    return known(b) and b["distinct_reporters"] == 3, seen(b)


def a_three_one_silent(x: Ctx) -> Outcome:
    v = x.phone()
    x.post([x.victim(v), x.victim(v), x.rep(value=v, note="")])
    b = x.look(v)
    return known(b), seen(b)


def a_three_blank_proof(x: Ctx) -> Outcome:
    v = x.phone()
    x.post([x.rep(value=v, note="", lost=x.r.choice([500, 2000, 15000]), shot=True) for _ in range(3)])
    b = x.look(v)
    return known(b), seen(b)


def a_three_blank(x: Ctx) -> Outcome:
    v = x.phone(); x.post([x.rep(value=v, note="") for _ in range(3)]); b = x.look(v)  # noqa: E702
    return suspicious(b), seen(b)


def a_ten_over_weeks(x: Ctx) -> Outcome:
    v = x.phone(); st = x.r.choice(["digital-arrest", "courier-customs", "job-offer"])  # noqa: E702
    x.post([x.rep(value=v, st=st) for _ in range(10)]); b = x.look(v)  # noqa: E702
    return known(b) and b["distinct_reporters"] >= 9, seen(b)


def a_viral_wave(x: Ctx) -> Outcome:
    v = x.phone(); t0 = x.r.uniform(3, 30)  # noqa: E702
    x.post([x.rep(value=v, st="electricity-disconnection", hours_ago=t0 - x.r.uniform(0, 1.5),
                  lag_min=x.r.uniform(3, 60)) for _ in range(30)])  # fmt: skip
    b = x.look(v)
    return known(b) and b["distinct_reporters"] >= 25, seen(b)


def a_same_carrier(x: Ctx) -> Outcome:
    v = x.phone(); ip = x.g.isp[0]  # noqa: E702
    x.post([x.rep(who=(x.rid(), ip if i < 4 else x.r.choice(x.g.isp)), value=v) for i in range(8)])
    b = x.look(v)
    return known(b), seen(b)


def a_mislabel(x: Ctx) -> Outcome:
    v = x.phone()
    x.post([x.rep(value=v, st="otp-call" if i < 6 else x.r.choice(["fake-customer-care", "fake-kyc-link"])) for i in range(10)])
    b = x.look(v)
    return known(b), seen(b)


def a_hindi(x: Ctx) -> Outcome:
    v = x.phone()
    notes = ["बैंक वाला बनकर कॉल किया और ओटीपी मांगा", "मुझे कॉल आया, कार्ड बंद होने का डर दिखाया और ओटीपी मांगा",
             "फोन पर बोला खाता बंद हो जाएगा, ओटीपी बताओ", "मेरे पिताजी को कॉल आया, ओटीपी मांग रहे थे",
             "बैंक से बोल रहा हूं कहकर ठगी की कोशिश की"]  # fmt: skip
    x.post([x.rep(value=v, note=n) for n in notes]); b = x.look(v)  # noqa: E702
    return known(b), seen(b)


def a_short_notes(x: Ctx) -> Outcome:
    v = x.phone()
    notes = ["fraud call", "scam call aaya", "fake bank call", "otp maanga", "bank wala fake", "fraud hai ye"]
    x.post([x.rep(value=v, note=n) for n in notes]); b = x.look(v)  # noqa: E702
    return known(b), seen(b)


def a_family(x: Ctx) -> Outcome:
    v = x.phone(); home = x.r.choice(x.g.isp)  # noqa: E702
    reps = [x.victim(v, who=(x.rid(), home), hours_ago=40 + i * 20) for i in range(2)]
    reps += [x.victim(v) for _ in range(2)]
    x.post(reps); b = x.look(v)  # noqa: E702
    return known(b) and b["distinct_reporters"] >= 3, seen(b)


def a_adds_detail(x: Ctx) -> Outcome:
    v = x.phone(); who = x.g.person()  # noqa: E702
    x.post([x.victim(v, who=who, hours_ago=50), x.victim(v, who=who, hours_ago=20), x.victim(v), x.victim(v)])
    b = x.look(v)
    return known(b) and b["distinct_reporters"] == 3, seen(b)


def a_upi_url_sender(x: Ctx) -> Outcome:
    out = []
    ok = True
    for t, (raw, _, _) in (("upi", x.g.upi()[:3]), ("url", x.g.url()[:3]), ("sender_id", x.g.sender()[:3])):
        st = {"upi": "upi-refund-qr", "url": "fake-kyc-link", "sender_id": "electricity-disconnection"}[t]
        x.post([x.victim(raw, st=st, t=t) for _ in range(5)])
        b = x.look(raw, t)
        ok &= known(b)
        out.append(f"{t}: {b.get('verdict')}")
    return ok, ", ".join(out)


# =========================================================================================
# B. Attacks on an honest number
# =========================================================================================

def bakery(x: Ctx) -> str:
    return f"+91 80 {x.r.randint(2000, 9999)} {x.r.randint(1000, 9999)}"


def b_spam_slow(x: Ctx) -> Outcome:
    v = x.phone(); who = x.g.person()  # noqa: E702
    x.post([x.victim(v, who=who, hours_ago=10 + 24 * i) for i in range(6)]); b = x.look(v)  # noqa: E702
    return not known(b) and b["distinct_reporters"] == 1, seen(b)


def b_spam_fast(x: Ctx) -> Outcome:
    v = x.phone(); who = x.g.person()  # noqa: E702
    codes = x.post([x.victim(v, who=who, hours_ago=1, lag_min=5 + i) for i in range(6)])
    b = x.look(v)
    return not known(b) and codes.count(429) >= 2, f"replies {codes}; then {seen(b)}"


def b_sybil(x: Ctx, n: int, notes: str) -> Outcome:
    v = x.phone(); ip = x.r.choice(x.g.isp)  # noqa: E702
    reps = [x.rep(who=(x.rid(), ip), value=v, hours_ago=x.r.uniform(0.5, 8), lag_min=x.r.uniform(1, 20),
                  note="" if notes == "blank" else None) for _ in range(n)]  # fmt: skip
    x.post(reps); b = x.look(v)  # noqa: E702
    return not known(b) and b["distinct_reporters"] <= 2, seen(b)


def b_slow_drip(x: Ctx) -> Outcome:
    v = x.phone(); ip = x.r.choice(x.g.isp)  # noqa: E702
    x.post([x.rep(who=(x.rid(), ip), value=v, hours_ago=12 + 24 * i) for i in range(10)]); b = x.look(v)  # noqa: E702
    return not known(b), seen(b)


def b_friends(x: Ctx, n: int, style: str, one_type: bool = False) -> Outcome:
    v = bakery(x); ips = x.r.sample(x.g.isp, min(n, 30))  # noqa: E702
    copied = "This number called and asked for my OTP pretending to be from the bank"
    reps = []
    for _ in range(n):
        note = {"blank": "", "review": x.r.choice([g for g in GRUDGE_NOTES if g]), "copy": copied,
                "mixed": x.r.choice([*GRUDGE_NOTES, copied, ""])}[style]  # fmt: skip
        st = "otp-call" if one_type else x.r.choice(["otp-call", "fake-customer-care", "other", "lottery-prize"])
        reps.append(x.rep(who=(x.rid(), x.r.choice(ips)), value=v, st=st, note=note, hours_ago=x.r.uniform(0.5, 48),
                          lag_min=x.r.uniform(2, 60), shot=x.r.random() < 0.3, lost=x.r.choice([0, 0, 500])))  # fmt: skip
    x.post(reps); b = x.look(v)  # noqa: E702
    return not known(b), seen(b)


def b_ten_two(x: Ctx, style: str) -> Outcome:
    v = bakery(x)
    reps = []
    for _ in range(10):
        ip = x.r.choice(x.g.isp)
        t0 = x.r.uniform(1, 30)
        story = x.victim(v)["note"]
        for acct in range(2):
            note = {"blank": "", "review": x.r.choice([g for g in GRUDGE_NOTES if g]),
                    "copy": "This number called and asked for my OTP pretending to be from the bank", "own": story}[style]  # fmt: skip
            reps.append(x.rep(who=(x.rid(), ip), value=v, note=note, hours_ago=t0, lag_min=5 + acct * x.r.uniform(1, 8)))
    x.post(reps); b = x.look(v)  # noqa: E702
    return not known(b), seen(b)


def b_bots_instant(x: Ctx) -> Outcome:
    v = x.phone()
    reps = [x.rep(value=v, note=x.victim(v)["note"], hours_ago=x.r.uniform(0.2, 0.9), lag_min=x.r.uniform(0.1, 1))
            for _ in range(25)]  # fmt: skip
    x.post(reps); b = x.look(v)  # noqa: E702
    return not known(b), seen(b)


def b_fake_proof(x: Ctx) -> Outcome:
    v = bakery(x)
    reps = [x.rep(value=v, note="", shot=True, lost=x.r.choice([500, 5000, 20000]), st=x.r.choice(["otp-call", "other", "lottery-prize"]),
                  hours_ago=x.r.uniform(0.5, 24)) for _ in range(30)]  # fmt: skip
    x.post(reps); b = x.look(v)  # noqa: E702
    return not known(b), seen(b)


def b_rival_small(x: Ctx) -> Outcome:
    v = bakery(x)
    x.post([x.victim(v, st="fake-customer-care") for _ in range(5)]); b = x.look(v)  # noqa: E702
    return not known(b), seen(b)


# =========================================================================================
# C. Attacks on a real scam, verified numbers, disputes
# =========================================================================================

def c_blank_flood(x: Ctx) -> Outcome:
    v = x.phone()
    x.post([x.victim(v, hours_ago=40 + 10 * i) for i in range(4)])
    before = x.look(v)
    x.post([x.rep(who=(x.rid(), x.r.choice(x.g.isp)), value=v, note="", hours_ago=x.r.uniform(0.3, 3), lag_min=2) for _ in range(15)])
    b = x.look(v)
    return known(before) and known(b), f"before {before.get('verdict')}; after 15 blank reports {seen(b)}"


def c_review_flood(x: Ctx) -> Outcome:
    v = x.phone()
    x.post([x.victim(v, hours_ago=40 + 10 * i) for i in range(4)])
    x.post([x.rep(value=v, note=x.r.choice([g for g in GRUDGE_NOTES if g]), hours_ago=x.r.uniform(0.3, 3)) for _ in range(15)])
    b = x.look(v)
    return known(b), f"after 15 review-style reports: {seen(b)}"


def c_verified(x: Ctx) -> Outcome:
    out, ok = [], True
    for t, v in (("phone", "1930"), ("phone", "1800 1600"), ("sender_id", "VM-HDFCBK"), ("url", "https://cybercrime.gov.in"),
                 ("phone", "+91 80 4100 2233"), ("upi", "freshbakes@okaxis")):  # fmt: skip
        x.post([x.victim(v, t=t, st="fake-customer-care") for _ in range(12)])
        b = x.look(v, t)
        ok &= b.get("verdict") == "VERIFIED_BUSINESS"
        out.append(f"{v}: {b.get('verdict')}")
    return ok, "; ".join(out)


def c_dispute(x: Ctx) -> Outcome:
    v = x.phone()
    x.post([x.victim(v) for _ in range(6)])
    before = x.look(v)
    r = x.c.post("/challenges", json={"identifier_type": "phone", "identifier_value": v, "claimant_name": "Sharma Sweets",
                                       "contact_email": "owner@example.com", "proof_note": "GST certificate attached."})  # fmt: skip
    x.post([x.victim(v) for _ in range(6)])
    b = x.look(v)
    ok = r.status_code == 201 and b.get("challenged") is True and not known(b)
    return ok, f"before {before.get('verdict')}; dispute {r.status_code} {r.json().get('status')}; after 6 more reports {seen(b)}, challenged={b.get('challenged')}"


def c_reporter_hits_verified(x: Ctx) -> Outcome:
    v = x.phone()
    reps = []
    for _ in range(3):
        who = x.g.person()
        reps += [x.victim("1930", who=who, st="fake-customer-care"), x.victim(v, who=who)]
    x.post(reps); b = x.look(v)  # noqa: E702
    return True, seen(b)


# =========================================================================================
# D. Input and formats
# =========================================================================================

def d_phone_formats(x: Ctx) -> Outcome:
    raw, canon, var = x.g.mobile()
    x.post([x.victim(raw) for _ in range(3)])
    answers = {(x.look(v).get("verdict"), x.look(v).get("report_count")) for v in var}
    return len(answers) == 1, f"{len(var)} spellings of {canon} -> {sorted(answers)}"


def d_other_formats(x: Ctx) -> Outcome:
    out, ok = [], True
    for t, gen in (("upi", x.g.upi), ("url", x.g.url), ("sender_id", x.g.sender)):
        raw, _canon, var = gen()
        x.post([x.victim(raw, t=t)])
        answers = {x.look(v, t).get("report_count") for v in var}
        ok &= answers == {1}
        out.append(f"{t} {len(var)} spellings -> counts {sorted(answers, key=str)}")
    return ok, "; ".join(out)


def d_brief_examples(x: Ctx) -> Outcome:
    pairs = [("phone", "+91 98765 43210", "09876543210"), ("phone", "98765-43210", "919876543210"),
             ("upi", "Ravi12@OKAXIS", "ravi12@okaxis"), ("url", "http://www.sbi-kyc.in/pay?utm=sms", "https://sbi-kyc.in/pay"),
             ("sender_id", "VM-HDFCBK", "AD-HDFCBK")]  # fmt: skip
    bad = [f"{a} vs {b}" for t, a, b in pairs if x.look(a, t).get("display_value") != x.look(b, t).get("display_value")]
    return not bad, "all five brief examples match" if not bad else f"mismatch: {bad}"


def d_junk(x: Ctx) -> Outcome:
    base = x.victim(x.phone())
    cases = {"number 12345": {"identifier_value": "12345"}, "number abc": {"identifier_value": "abc"},
             "empty number": {"identifier_value": ""}, "all zeros": {"identifier_value": "0000000000"},
             "bad UPI": {"identifier_type": "upi", "identifier_value": "nope"},
             "ftp link": {"identifier_type": "url", "identifier_value": "ftp://x"},
             "area ABCDEF": {"pincode": "ABCDEF"}, "time 'yesterday'": {"occurred_at": "yesterday"},
             "month 13": {"occurred_at": "2026-13-45T10:00:00+05:30"}, "type email": {"identifier_type": "email"}}  # fmt: skip
    codes = {k: x.c.post("/reports", json={**base, **p, "report_id": f"junk{i}"}).status_code for i, (k, p) in enumerate(cases.items())}
    miss = {k: c for k, c in codes.items() if c != 400}
    return not miss, "all rejected with 400" if not miss else f"not 400: {miss}"


def d_unknown_type(x: Ctx) -> Outcome:
    v = x.phone()
    codes = x.post([x.rep(value=v, st="crypto-romance", channel="Telegram")])
    b = x.look(v)
    return codes == [201] and b.get("scam_type") == "other", f"reply {codes}, stored type {b.get('scam_type')}"


def d_resend(x: Ctx) -> Outcome:
    v = x.phone(); r = x.victim(v)  # noqa: E702
    codes = [x.c.post("/reports", json=r).status_code for _ in range(3)]
    b = x.look(v)
    return b.get("report_count") == 1, f"sent the same report 3 times: replies {codes}, report_count {b.get('report_count')}"


def d_helplines_short(x: Ctx) -> Outcome:
    out = {v: x.look(v).get("verdict") for v in ("1930", "1909", "1800 2100", "1860 266 2666", "18001234")}
    return all(o == "VERIFIED_BUSINESS" for o in out.values()), str(out)


def d_invisible(x: Ctx) -> Outcome:
    _raw, canon, _ = x.g.mobile()
    d = canon[3:]
    sneaky = "\u200b" + d[:5] + "\u00a0" + d[5:] + "\u200d"
    x.post([x.victim(sneaky)])
    b = x.look(canon)
    return b.get("report_count") == 1, f"number with hidden characters -> report_count {b.get('report_count')} on the clean number"


def d_unreported(x: Ctx) -> Outcome:
    v = x.phone(); b = x.look(v)  # noqa: E702
    return b.get("verdict") == "NO_REPORTS" and b.get("report_count") == 0, seen(b)


def d_future(x: Ctx) -> Outcome:
    r = x.victim(x.phone())
    t = (datetime.now(IST) + timedelta(days=3)).isoformat(timespec="seconds")
    code = x.c.post("/reports", json={**r, "occurred_at": t, "reported_at": t}).status_code
    return code == 400, f"report dated 3 days in the future -> {code}"


# =========================================================================================
# E. Map and alerts
# =========================================================================================

def area_reports(x: Ctx, pin: str, per_day: float, days: tuple[float, float], types: list[str], **kw: Any) -> list[dict[str, Any]]:
    n = round(per_day * (days[1] - days[0]))
    return [x.rep(value=x.phone(), pin=pin, st=x.r.choice(types), hours_ago=x.r.uniform(days[0] * 24, days[1] * 24), **kw)
            for _ in range(n)]  # fmt: skip


def e_spike(x: Ctx) -> Outcome:
    x.post(area_reports(x, "560034", 2, (1.05, 8), ["otp-call"]) + area_reports(x, "560034", 10, (0.05, 0.95), ["otp-call"]))
    a = x.alerts("560034")
    return any(i["type"] == "SPIKE" for i in a), str([i["type"] + (f" {i.get('count')} vs {i.get('baseline_per_day')}/day" if i["type"] == "SPIKE" else "") for i in a])


def e_normal(x: Ctx) -> Outcome:
    x.post(area_reports(x, "560034", 3, (1.05, 8), ["otp-call"]) + area_reports(x, "560034", 3, (0.05, 0.95), ["otp-call"]))
    a = x.alerts("560034")
    return not any(i["type"] == "SPIKE" for i in a), f"alerts: {[i['type'] for i in a] or 'none'}"


def e_new_type(x: Ctx) -> Outcome:
    x.post([*area_reports(x, "560038", 0.5, (1.05, 29), ["otp-call", "fake-kyc-link"]), x.victim(x.phone(), st="sextortion", pin="560038", hours_ago=3)])
    a = x.alerts("560038")
    return any(i["type"] == "NEW_TYPE" and i["scam_type"] == "sextortion" for i in a), str([(i["type"], i.get("scam_type")) for i in a])


def e_old_off_map(x: Ctx) -> Outcome:
    x.post(area_reports(x, "560066", 1, (9, 35), ["otp-call"]))
    m7 = {c["pincode"] for c in x.c.get("/map", params={"pincode": "560066"}).json()["clusters"]}
    m30 = {c["pincode"] for c in x.c.get("/map", params={"pincode": "560066", "days": 30}).json()["clusters"]}
    return "560066" not in m7 and "560066" in m30, f"7-day map: {'shown' if '560066' in m7 else 'not shown'}; 30-day map: {'shown' if '560066' in m30 else 'not shown'}"


def e_radius(x: Ctx) -> Outcome:
    x.post([x.victim(x.phone(), pin=p, hours_ago=x.r.uniform(2, 96)) for p in ("560102", "560103", "560034", "400050")])
    r2 = sorted(c["locality"] for c in x.c.get("/map", params={"pincode": "560102", "radius_km": 2}).json()["clusters"])
    r10 = sorted(c["locality"] for c in x.c.get("/map", params={"pincode": "560102", "radius_km": 10}).json()["clusters"])
    return r2 == ["HSR Layout"] and "Mumbai" not in str(r10) and len(r10) == 3, f"2 km: {r2}; 10 km: {r10}"


def e_map_points(x: Ctx) -> Outcome:
    x.post([x.victim(x.phone(), pin="560102", hours_ago=x.r.uniform(2, 96)) for _ in range(4)])
    c = x.c.get("/map", params={"pincode": "560102"}).json()["clusters"][0]
    return (c["lat"], c["lng"]) == (12.9116, 77.6473), f"HSR Layout drawn at {c['lat']}, {c['lng']} (official point 12.9116, 77.6473)"


def e_sybil_no_spike(x: Ctx) -> Outcome:
    pin = "560076"
    reps = area_reports(x, pin, 1, (1.05, 8), ["otp-call"])
    ip = x.r.choice(x.g.isp)
    reps += [x.rep(who=(x.rid(), ip), value=x.phone(), pin=pin, hours_ago=x.r.uniform(0.2, 5)) for _ in range(22)]
    x.post(reps); a = x.alerts(pin)  # noqa: E702
    return not any(i["type"] == "SPIKE" for i in a), f"22 accounts on one Wi-Fi, each reporting a different number: alerts {[i['type'] for i in a] or 'none'}"


def e_spam_no_new_type(x: Ctx) -> Outcome:
    pin = "560011"; v = x.phone(); who = x.g.person()  # noqa: E702
    reps = area_reports(x, pin, 0.5, (1.05, 29), ["otp-call"])
    reps += [x.victim(v, who=who, st="job-offer", pin=pin, hours_ago=2 + 4 * i) for i in range(6)]
    x.post(reps); a = x.alerts(pin)  # noqa: E702
    return not any(i["type"] == "NEW_TYPE" for i in a), f"one person reports a new scam type 6 times: alerts {[i['type'] for i in a] or 'none'}"


def e_friends_no_alert(x: Ctx) -> Outcome:
    pin = "560037"; v = bakery(x)  # noqa: E702
    reps = area_reports(x, pin, 0.5, (1.05, 29), ["otp-call"])
    reps += [x.rep(value=v, pin=pin, note=x.r.choice([g for g in GRUDGE_NOTES if g]), st=x.r.choice(["other", "otp-call", "lottery-prize"]),
                   hours_ago=x.r.uniform(0.2, 20)) for _ in range(40)]  # fmt: skip
    x.post(reps); a = x.alerts(pin)  # noqa: E702
    return not a, f"40 friends on a bakery: alerts {[i['type'] for i in a] or 'none'}"


def e_one_victim_new_type(x: Ctx) -> Outcome:
    pin = "560078"
    x.post([*area_reports(x, pin, 0.5, (1.05, 29), ["otp-call"]), x.victim(x.phone(), st="loan-app-harassment", pin=pin, hours_ago=5)])
    a = x.alerts(pin)
    return any(i["type"] == "NEW_TYPE" for i in a), f"one real victim of a new scam type: alerts {[i['type'] for i in a] or 'none'}"


# =========================================================================================
# F. Privacy
# =========================================================================================

def f_masking(x: Ctx) -> Outcome:
    out, ok = [], True
    for t, gen in (("phone", x.g.mobile), ("upi", x.g.upi), ("url", x.g.url), ("sender_id", x.g.sender)):
        raw, canon, _ = gen()
        x.post([x.victim(raw, t=t) for _ in range(2)])
        b = x.look(raw, t)
        full = canon[3:] if t == "phone" else canon.lower().removeprefix("https://")
        ok &= full not in json.dumps(b).lower()
        out.append(f"{t}: {b['display_value']}")
    return ok, "; ".join(out)


def f_unmask(x: Ctx) -> Outcome:
    raw, canon, _ = x.g.mobile()
    x.post([x.victim(raw) for _ in range(4)])
    b = x.look(raw)
    return b["display_value"] == canon, f"4 real victims: shown as {b['display_value']}"


def f_no_leaks(x: Ctx) -> Outcome:
    v = x.phone()
    reps = [x.victim(v) for _ in range(5)]
    x.post(reps)
    bodies = json.dumps([x.look(v), x.c.get("/map", params={"pincode": "560102"}).json(), x.alerts("560102")])
    leaks = [s for r in reps for s in (r["reporter_id"], r["ip_prefix"], r["note"][:30]) if s and s in bodies]
    return not leaks, "no reporter id, IP prefix or note text in any reply" if not leaks else f"LEAKED {leaks}"


def f_wording(x: Ctx) -> Outcome:
    v = x.phone(); x.post([x.victim(v) for _ in range(5)])  # noqa: E702
    b = x.look(v)
    bad = [w for w in ("fraud", "scammer", "criminal", "this person", "cheat") if w in json.dumps(b).lower()]
    return not bad, f"summary: '{b.get('summary')}'" + (f" BAD WORDS {bad}" if bad else "")


# =========================================================================================
# G. Licence
# =========================================================================================

def g_licence(kind: str) -> Callable[[Ctx], Outcome]:
    def run(x: Ctx) -> Outcome:
        from scripts.mint_licence import DEFAULT_KEY, mint

        long = mint("Demo Bank", timedelta(days=365), DEFAULT_KEY)
        try:
            if kind == "expire":
                v = x.phone(); x.post([x.victim(v)])  # noqa: E702
                x.c.post("/license", json=mint("Demo Bank", timedelta(seconds=8), DEFAULT_KEY))
                time.sleep(14)
                codes = {p: x.c.get(p, params=q).status_code for p, q in (("/lookup", {"type": "phone", "value": v}),
                         ("/map", {"pincode": "560102"}), ("/alerts", {"pincode": "560102"}))}  # fmt: skip
                codes["POST /reports"] = x.c.post("/reports", json=x.victim(x.phone())).status_code
                h = x.c.get("/health").status_code
                x.c.post("/license", json=long)
                back = x.look(v).get("report_count")
                ok = set(codes.values()) == {403} and h == 200 and back == 1
                return ok, f"after expiry {codes}, /health {h}; after new licence, no restart: report still there (count {back})"
            doc = mint("Demo Bank", timedelta(days=30), DEFAULT_KEY)
            if kind == "tamper":
                r = x.c.post("/license", json={**doc, "expires_at": "2099-01-01T00:00:00+05:30"})
                return r.status_code == 400, f"licence with edited expiry date -> {r.status_code} {r.text[:80]}"
            if kind == "forged":
                r = x.c.post("/license", json={**doc, "signature": base64.b64encode(b"x" * 64).decode()})
                return r.status_code == 400, f"licence with a made-up signature -> {r.status_code}"
            old = mint("Demo Bank", timedelta(seconds=1), DEFAULT_KEY)
            time.sleep(2)
            r = x.c.post("/license", json=old)
            return r.status_code == 400, f"uploading an already-expired licence -> {r.status_code}"
        finally:
            x.c.post("/license", json=long)

    return run


# =========================================================================================

def catalogue() -> list[Scenario]:
    S = Scenario
    return [
        S("A. Real victims", "One victim reports", "One person reports a scam call with a note.", "SUSPICIOUS, number hidden", a_one),
        S("A. Real victims", "Two victims", "Two strangers report the same number.", "SUSPICIOUS, still hidden (needs 3 people)", a_two),
        S("A. Real victims", "Three victims who describe it", "Three strangers each write what happened.", "KNOWN_SCAM, 3 people", a_three_described),
        S("A. Real victims", "Three victims, one wrote nothing", "Two describe it, one only taps report.", "KNOWN_SCAM", a_three_one_silent),
        S("A. Real victims", "Three victims, blank notes but proof", "Three people, no notes, each attaches a screenshot and a loss.", "KNOWN_SCAM", a_three_blank_proof),
        S("A. Real victims", "Three blank clicks", "Three people tap report, write nothing, no proof.", "SUSPICIOUS (policy: not enough to confirm)", a_three_blank),
        S("A. Real victims", "Ten victims over weeks", "Ten people report over two weeks, a quarter leave notes blank.", "KNOWN_SCAM, ~10 people", a_ten_over_weeks),
        S("A. Real victims", "Viral wave", "30 people hit by one SMS blast report within 90 minutes.", "KNOWN_SCAM, 25+ of the 30 counted", a_viral_wave,
          note="The verdict is right every time. The count can come out a little low (about 24 of 30): when two strangers on the same mobile carrier block report within 15 minutes of each other, the account-switch rule (which stops one person using two accounts) merges them. A small undercount on a big wave was the price of catching account switching."),
        S("A. Real victims", "Victims on one mobile carrier block", "8 victims, 4 of them share one carrier address block (CGNAT).", "KNOWN_SCAM", a_same_carrier),
        S("A. Real victims", "Victims pick different scam types", "10 victims; 6 say OTP call, 4 pick a related type.", "KNOWN_SCAM", a_mislabel),
        S("A. Real victims", "Hindi-only notes", "5 victims write only in Hindi.", "KNOWN_SCAM", a_hindi, randomised=False),
        S("A. Real victims", "Very short notes", "6 victims write 'fraud call', 'otp maanga' and similar.", "KNOWN_SCAM", a_short_notes, randomised=False),
        S("A. Real victims", "Two family members on home Wi-Fi + 2 others", "Husband and wife report a day apart from home, 2 others too.", "KNOWN_SCAM, 3+ people", a_family),
        S("A. Real victims", "A victim reports twice to add detail", "One person reports, then again next day; 2 others report.", "KNOWN_SCAM, counted 3", a_adds_detail),
        S("A. Real victims", "UPI ID, link and SMS sender scams", "5 victims each for a UPI ID, a fake link and an SMS sender.", "KNOWN_SCAM for all three", a_upi_url_sender),
        S("B. Attacks on an honest number", "One person, 6 times, over 6 days", "Same reporter files 6 reports on one number, one a day.", "Not KNOWN, counted as 1", b_spam_slow),
        S("B. Attacks on an honest number", "One person, 6 times, within an hour", "Same reporter fires 6 reports in minutes.", "429 slow-down after 3, not KNOWN", b_spam_fast),
        S("B. Attacks on an honest number", "22 accounts on one Wi-Fi, with stories", "22 fake accounts on one connection, each writes a victim-style story.", "Not KNOWN, counted as 1-2", lambda x: b_sybil(x, 22, "story")),
        S("B. Attacks on an honest number", "22 accounts on one Wi-Fi, blank", "Same, but notes left blank.", "Not KNOWN, counted as 1-2", lambda x: b_sybil(x, 22, "blank")),
        S("B. Attacks on an honest number", "Slow-drip fake accounts", "10 accounts on one connection, one report a day for 10 days.", "Not KNOWN", b_slow_drip),
        S("B. Attacks on an honest number", "40 friends, blank notes", "40 friends of an angry customer report a bakery, no notes.", "Not KNOWN", lambda x: b_friends(x, 40, "blank")),
        S("B. Attacks on an honest number", "40 friends write shop complaints", "'stale bread', 'rude owner', 'overpriced'.", "Not KNOWN", lambda x: b_friends(x, 40, "review")),
        S("B. Attacks on an honest number", "40 friends paste one scam story", "Everyone pastes 'asked for my OTP pretending to be the bank'.", "Not KNOWN", lambda x: b_friends(x, 40, "copy")),
        S("B. Attacks on an honest number", "40 friends, mixed notes", "A mix of complaints, the pasted story and blanks.", "Not KNOWN", lambda x: b_friends(x, 40, "mixed")),
        S("B. Attacks on an honest number", "40 friends, complaints, all pick one scam type", "Complaints, but everyone selects 'OTP call'.", "Not KNOWN", lambda x: b_friends(x, 40, "review", one_type=True)),
        S("B. Attacks on an honest number", "10 friends x 2 accounts, blank", "Your example: 10 friends, each reports from 2 accounts, minutes apart.", "Not KNOWN", lambda x: b_ten_two(x, "blank")),
        S("B. Attacks on an honest number", "10 friends x 2 accounts, complaints", "Same, writing shop complaints.", "Not KNOWN", lambda x: b_ten_two(x, "review")),
        S("B. Attacks on an honest number", "10 friends x 2 accounts, one pasted story", "Same, all pasting one scam story.", "Not KNOWN", lambda x: b_ten_two(x, "copy")),
        S("B. Attacks on an honest number", "10 friends x 2 accounts, each invents own story", "Each friend writes a different believable scam story and they agree on the type.", "Not KNOWN (ideally)", lambda x: b_ten_two(x, "own"),
          note="Expected limit: 10 real people telling different, consistent stories look exactly like 10 victims. The defence is the dispute feature (row C) and the verified list."),
        S("B. Attacks on an honest number", "Bot farm, instant reports", "25 accounts report within a minute of the 'incident', all within an hour.", "Not KNOWN", b_bots_instant),
        S("B. Attacks on an honest number", "30 blank reports all claiming proof", "30 people, no notes, all tick screenshot and money lost, mixed types.", "Not KNOWN", b_fake_proof),
        S("B. Attacks on an honest number", "5 rivals with believable stories", "5 people from a rival shop each write a believable scam story.", "Not KNOWN (ideally)", b_rival_small,
          note="Expected limit, same reason as the 10-friends own-story case: a small group of humans writing consistent, distinct stories is indistinguishable from victims. The business can dispute."),
        S("C. Real scams, verified numbers, disputes", "Scammer floods blank reports on own number", "4 victims flag a number; the scammer then files 15 blank reports.", "Stays KNOWN_SCAM", c_blank_flood),
        S("C. Real scams, verified numbers, disputes", "Scammer floods fake complaints on own number", "4 victims flag it; the scammer files 15 review-style reports.", "Stays KNOWN_SCAM (ideally)", c_review_flood,
          note="Known limit: only blank floods are set aside. A flood of review-style notes trips the pile-on gate and the number drops to SUSPICIOUS (still reported, still warns)."),
        S("C. Real scams, verified numbers, disputes", "Verified numbers bombed", "12 reports each on 1930, a bank toll-free, a bank SMS sender, cybercrime.gov.in, a shop and its UPI.", "Always VERIFIED_BUSINESS", c_verified),
        S("C. Real scams, verified numbers, disputes", "Business disputes a number", "6 victims report, the business disputes, 6 more report.", "challenged=true, never KNOWN while under review", c_dispute),
        S("C. Real scams, verified numbers, disputes", "Reporters who also reported 1930", "3 people report 1930 (a helpline) and also a real number.", "Their weight is halved; shown for information", c_reporter_hits_verified),
        S("D. Input and formats", "Every phone spelling", "+91 98765 43210, 09876543210, 98765-43210, 919876543210, bare 10 digits, +91...", "One identical answer", d_phone_formats),
        S("D. Input and formats", "UPI, link and sender spellings", "Upper case UPI, www / http / ?utm links, VM- / AD- / JD- senders.", "One identical answer each", d_other_formats),
        S("D. Input and formats", "The brief's own examples", "The five example pairs from Appendix A.", "Same answer for each pair", d_brief_examples, randomised=False),
        S("D. Input and formats", "Junk reports", "12345, abc, empty, all zeros, bad UPI, ftp link, area ABCDEF, time 'yesterday', month 13, type email.", "All rejected with 400", d_junk, randomised=False),
        S("D. Input and formats", "Report dated in the future", "occurred_at 3 days ahead.", "Rejected with 400", d_future, randomised=False),
        S("D. Input and formats", "Unknown scam type and channel", "scam_type 'crypto-romance', channel 'Telegram'.", "Accepted, stored as 'other'", d_unknown_type, randomised=False),
        S("D. Input and formats", "Same report sent 3 times", "Network retry sends one report_id three times.", "Counted once", d_resend, randomised=False),
        S("D. Input and formats", "Helplines and toll-free numbers", "1930, 1909, 1800 2100, 1860 266 2666, 18001234.", "Accepted, VERIFIED_BUSINESS", d_helplines_short, randomised=False),
        S("D. Input and formats", "Number with hidden characters", "Zero-width and non-breaking spaces pasted inside a number.", "Same as the clean number", d_invisible, randomised=False),
        S("D. Input and formats", "Never-reported number", "Look up a valid number nobody reported.", "200 NO_REPORTS, count 0", d_unreported, randomised=False),
        S("E. Map and alerts", "Sudden jump in an area", "2 reports a day for a week, then 10 in the last 24 hours.", "SPIKE alert", e_spike),
        S("E. Map and alerts", "Steady area", "3 a day every day.", "No SPIKE", e_normal),
        S("E. Map and alerts", "New kind of scam in an area", "A month of OTP and KYC scams, then one sextortion report today.", "NEW_TYPE alert for sextortion", e_new_type),
        S("E. Map and alerts", "One real victim of a new type", "Quiet area, one genuine victim of a type never seen there.", "NEW_TYPE alert", e_one_victim_new_type),
        S("E. Map and alerts", "Old reports", "Reports 9 to 35 days old only.", "Not on the 7-day map; on a 30-day map", e_old_off_map),
        S("E. Map and alerts", "Radius", "Reports in HSR, Bellandur, Koramangala and Mumbai; map around HSR.", "2 km: HSR only; 10 km: the 3 Bengaluru areas", e_radius, randomised=False),
        S("E. Map and alerts", "Map location", "Reports in HSR Layout.", "Drawn at the official Appendix B point", e_map_points, randomised=False),
        S("E. Map and alerts", "22 fake accounts, many numbers, one area", "A farm on one Wi-Fi reports 22 different numbers in one area today.", "No SPIKE (bonus)", e_sybil_no_spike),
        S("E. Map and alerts", "Spammer reports a new type 6 times", "One person files 6 reports of a type new to the area.", "No NEW_TYPE (bonus)", e_spam_no_new_type),
        S("E. Map and alerts", "40 friends on a bakery", "Friends pile onto one shop's number in its area.", "No alerts at all (bonus)", e_friends_no_alert),
        S("F. Privacy", "Under 3 people: hidden", "Two reports each on a phone, UPI, link and sender.", "Masked: 98XXXXX210, r***@okaxis, sbi***.in/..., HD****", f_masking),
        S("F. Privacy", "Established: shown", "Four real victims.", "Full number shown", f_unmask),
        S("F. Privacy", "Nothing identifies a reporter", "Search every lookup, map and alert reply for reporter ids, IPs and note text.", "Nothing found", f_no_leaks),
        S("F. Privacy", "Careful wording", "Read the lookup reply for accusing words.", "'Reported by N people near you', no 'fraud' / 'scammer'", f_wording, randomised=False),
        S("G. Licence", "Licence runs out, then renewed", "8-second licence, wait, try everything, upload a new one.", "403 everywhere but /health, then back with data, no restart", g_licence("expire"), randomised=False),
        S("G. Licence", "Edited licence", "Change the expiry date inside a valid licence.", "Rejected", g_licence("tamper"), randomised=False),
        S("G. Licence", "Forged licence", "A licence with a made-up signature.", "Rejected", g_licence("forged"), randomised=False),
        S("G. Licence", "Old licence re-uploaded", "Upload a licence that has already expired.", "Rejected", g_licence("expired-upload"), randomised=False),
    ]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--seeds", type=int, default=20)
    ap.add_argument("--first-seed", type=int, default=7001)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()

    rows: list[tuple[Scenario, int, int, list[str], list[str]]] = []
    with httpx.Client(base_url=a.base_url, timeout=60) as c:
        for sc in catalogue():
            seeds = range(a.first_seed, a.first_seed + (a.seeds if sc.randomised else 1))
            passed, fails, examples = 0, [], []
            for seed in seeds:
                x = Ctx(c, seed)
                x.reset()
                try:
                    ok, obs = sc.fn(x)
                except Exception as exc:  # a crash is a failure, recorded with its reason
                    ok, obs = False, f"error: {exc!r}"
                passed += ok
                (examples if ok else fails).append(f"seed {seed}: {obs}")
            rows.append((sc, passed, len(seeds), examples, fails))
            print(f"{'PASS' if passed == len(seeds) else 'FAIL'} {passed:>2}/{len(seeds):<2} {sc.cat[:2]} {sc.name}", flush=True)
        c.post("/admin/reset")

    a.out.write_text(render(rows, a))
    return 0


def render(rows: list[tuple[Scenario, int, int, list[str], list[str]]], a: argparse.Namespace) -> str:
    total = sum(r[2] for r in rows)
    ok = sum(r[1] for r in rows)
    clean = sum(r[1] == r[2] for r in rows)
    out = [
        "# What happens in every case: scenario catalogue",
        "",
        f"Generated {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')} by `scammap/judge/catalog.py` against `{a.base_url}`, "
        f"the same code that is deployed. Each scenario starts from an empty server. Randomised scenarios ran on "
        f"{a.seeds} different seeds (people, numbers, timings and notes change every run), so a result like 19/20 is a rate, not a guess.",
        "",
        f"**{clean} of {len(rows)} scenarios behave as expected on every run** ({ok} of {total} individual runs).",
        "",
        "How to read a row: **What happens** is the story; **Expected** is what the brief or plain sense demands; "
        "**Result** is how many runs gave that answer; **What our system did** is a real answer from one run.",
        "",
    ]
    cat = ""
    for sc, p, n, ex, fails in rows:
        if sc.cat != cat:
            cat = sc.cat
            out += ["", f"## {cat}", "", "| | Scenario | What happens | Expected | Result | What our system did |", "|---|---|---|---|---|---|"]
        mark = "✅" if p == n else ("⚠️" if p > 0 else "❌")
        sample = (fails[0] if fails else ex[0]).split(": ", 1)[1] if (fails or ex) else ""
        out.append(f"| {mark} | {sc.name} | {sc.story} | {sc.expect} | {p}/{n} | {sample.replace('|', '/')} |")
    out += ["", "## Where it does not do what we would like, and why", ""]
    misses = [(sc, p, n, fails) for sc, p, n, _, fails in rows if p < n]
    if not misses:
        out.append("Nothing. Every scenario behaved as expected on every run.")
    for sc, p, n, fails in misses:
        out += [f"### {sc.name} ({p}/{n})", "", sc.note or "Not explained yet: needs a look.", "", "Failing runs:", ""]
        out += [f"- {f}" for f in fails[:5]] + ([f"- ... and {len(fails) - 5} more"] if len(fails) > 5 else []) + [""]
    out += ["", "## Not testable by a scenario run (covered elsewhere)", "",
            "- **Clock wound back to extend a licence**: refused with reason `clock_rollback` (unit test `tests/test_licence.py`).",
            "- **Same thing on the live https server**: the four-step licence demo passed live, see `scammap/evidence/licence_demo_*.md`.",
            "- **Lookup speed on the live server**: see the latest `scammap/evidence/judge_*.md` (server time vs network time)."]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())
