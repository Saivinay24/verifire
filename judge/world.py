"""A judging-day world built only from the PRD, never from our own code.

Nothing here imports `app`. The judges load one mixed, secret dataset, so this builds one mixed
world per seed: genuine reporters who share mobile-carrier /24s, real scams reported over days,
low-report numbers, every trick from the brief at sizes above and below the stated ones, and
dedicated areas for spike / normal / new-type / old / fake-alert checks.

Each identifier carries the verdict the PRD demands, so the runner can grade without
knowing anything about how the server decides.
"""

from __future__ import annotations

import random
import string
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

IST = timezone(timedelta(hours=5, minutes=30))

# Appendix B, copied by hand from the PRD.
AREAS: dict[str, tuple[str, str, float, float]] = {
    "560102": ("HSR Layout", "Bengaluru", 12.9116, 77.6473),
    "560038": ("Indiranagar", "Bengaluru", 12.9784, 77.6408),
    "560034": ("Koramangala", "Bengaluru", 12.9352, 77.6245),
    "560066": ("Whitefield", "Bengaluru", 12.9698, 77.7500),
    "560076": ("BTM Layout", "Bengaluru", 12.9166, 77.6101),
    "560011": ("Jayanagar", "Bengaluru", 12.9299, 77.5826),
    "560037": ("Marathahalli", "Bengaluru", 12.9591, 77.6974),
    "560103": ("Bellandur", "Bengaluru", 12.9260, 77.6762),
    "560100": ("Electronic City", "Bengaluru", 12.8452, 77.6602),
    "560078": ("JP Nagar", "Bengaluru", 12.9077, 77.5851),
    "560003": ("Malleshwaram", "Bengaluru", 13.0035, 77.5709),
    "560010": ("Rajajinagar", "Bengaluru", 12.9915, 77.5520),
    "560024": ("Hebbal", "Bengaluru", 13.0358, 77.5970),
    "560064": ("Yelahanka", "Bengaluru", 13.1007, 77.5963),
    "560070": ("Banashankari", "Bengaluru", 12.9250, 77.5468),
    "400050": ("Bandra West", "Mumbai", 19.0596, 72.8295),
    "110016": ("Hauz Khas", "Delhi", 28.5494, 77.2001),
    "500081": ("Madhapur", "Hyderabad", 17.4486, 78.3908),
    "600020": ("Adyar", "Chennai", 13.0012, 80.2565),
    "411014": ("Viman Nagar", "Pune", 18.5679, 73.9143),
    "700091": ("Salt Lake Sector V", "Kolkata", 22.5790, 88.4290),
    "380015": ("Satellite", "Ahmedabad", 23.0260, 72.5085),
    "302017": ("Malviya Nagar", "Jaipur", 26.8570, 75.8080),
    "226010": ("Gomti Nagar", "Lucknow", 26.8540, 80.9990),
    "682030": ("Kakkanad", "Kochi", 10.0159, 76.3419),
}

# Appendix C. The channel a real victim would pick for each scam type.
TYPE_CHANNELS: dict[str, list[str]] = {
    "digital-arrest": ["Phone call"],
    "fake-kyc-link": ["SMS or WhatsApp", "Fake website"],
    "upi-refund-qr": ["QR code", "UPI request"],
    "investment-group": ["SMS or WhatsApp"],
    "courier-customs": ["Phone call", "SMS or WhatsApp"],
    "job-offer": ["SMS or WhatsApp"],
    "lottery-prize": ["SMS or WhatsApp", "Phone call"],
    "loan-app-harassment": ["Phone call", "SMS or WhatsApp"],
    "electricity-disconnection": ["SMS or WhatsApp"],
    "fake-customer-care": ["Phone call", "Fake website"],
    "otp-call": ["Phone call"],
    "sextortion": ["SMS or WhatsApp", "Phone call"],
}
TYPES = list(TYPE_CHANNELS)

VERIFIED: list[tuple[str, str]] = [
    ("phone", "1930"), ("phone", "1909"), ("phone", "1800 1600"), ("phone", "1800 2600"),
    ("phone", "1800 1080"), ("phone", "1800 1234"), ("phone", "1800 2100"),
    ("phone", "1860 419 5555"), ("phone", "1860 266 2666"),
    ("sender_id", "HDFCBK"), ("sender_id", "ICICIB"), ("sender_id", "SBIINB"),
    ("sender_id", "AXISBK"), ("sender_id", "KOTAKB"),
    ("url", "https://cybercrime.gov.in"), ("url", "https://sancharsaathi.gov.in"),
    ("phone", "+91 80 4100 2233"), ("phone", "+91 80 2553 0190"), ("upi", "freshbakes@okaxis"),
]  # fmt: skip

# What a victim writes. Built from parts (opener, what they claimed, what they wanted, how it ended)
# so two strangers almost never write the same sentence, as in real life. Mixed English/Hinglish/Hindi.
OPENERS = ["", "", "Got a call,", "Received a WhatsApp message,", "Unknown number contacted me,",
           "Mujhe call aaya,", "मुझे एक कॉल आया,", "My father got this,", "Yesterday evening",
           "Around 11am today", "My wife received this.", "Aaj subah", "Last week", "My neighbour also got it."]  # fmt: skip
CLAIMS: dict[str, list[str]] = {
    "digital-arrest": [
        "man in police uniform on video said I am under digital arrest",
        "fake CBI officer showed an arrest warrant on skype",
        "bola aapke Aadhaar se money laundering hua hai",
        "पुलिस वाला बनकर बोला आपके खिलाफ एफआईआर है",
    ],
    "fake-kyc-link": [
        "SMS said bank KYC expires today with a link",
        "message said account will be blocked, update PAN",
        "KYC update ka link bheja jo bank jaisa dikh raha tha",
        "केवाईसी अपडेट का लिंक आया",
    ],
    "upi-refund-qr": [
        "buyer sent a QR code to receive payment",
        "said refund is pending and sent a QR",
        "OLX pe kharidne wale ne QR bheja",
        "रिफंड के लिए क्यूआर कोड भेजा",
    ],
    "investment-group": [
        "added me to a stock trading WhatsApp group showing big profits",
        "investment tips group promised 30% weekly returns",
        "crypto trading app mein profit dikhaya",
        "इन्वेस्टमेंट ग्रुप में मुनाफा दिखाया",
    ],
    "courier-customs": [
        "said my FedEx parcel was held at customs with drugs",
        "courier company said package stuck in customs",
        "parcel customs mein ruka hai bola",
        "कूरियर वाले ने कहा पार्सल कस्टम में है",
    ],
    "job-offer": [
        "offered part time job liking youtube videos",
        "telegram task job paid small amount first",
        "work from home job ka offer diya",
        "घर बैठे नौकरी का ऑफर दिया",
    ],
    "lottery-prize": [
        "said I won a KBC lottery of 25 lakh",
        "lucky draw prize winner message",
        "bola aapka inaam nikla hai",
        "लॉटरी जीतने का मैसेज आया",
    ],
    "loan-app-harassment": [
        "loan app agents threatening to call my contacts",
        "instant loan app sending morphed photos",
        "loan wale gaali de rahe hain relatives ko",
        "लोन ऐप वाले धमकी दे रहे हैं",
    ],
    "electricity-disconnection": [
        "SMS said power will be cut tonight at 9:30",
        "electricity officer said bill not updated",
        "bijli kat jayegi bola aaj raat",
        "बिजली कटने का मैसेज आया",
    ],
    "fake-customer-care": [
        "searched customer care on google and this number answered",
        "fake bank helpline picked up",
        "customer care wala bankar baat ki",
        "कस्टमर केयर बनकर बात की",
    ],
    "otp-call": [
        "caller said he is from bank fraud team",
        "said card will be blocked and needs verification",
        "bank se bol raha hoon bola",
        "बैंक वाला बनकर कॉल किया",
    ],
    "sextortion": [
        "unknown video call recorded my screen",
        "video call then blackmail with edited video",
        "video call record karke dhamki di",
        "अनजान वीडियो कॉल के बाद ब्लैकमेल",
    ],
}
DEMANDS: dict[str, list[str]] = {
    "digital-arrest": [
        "and asked to transfer savings for verification",
        "told me not to tell family and stay on camera",
        "paise transfer karne ko bola",
        "पैसे मांगे",
    ],
    "fake-kyc-link": [
        "and the page asked for netbanking password",
        "link opened a fake login page",
        "login kiya toh paise kat gaye",
        "लिंक पर क्लिक करवाया",
    ],
    "upi-refund-qr": [
        "scanning it asked for my UPI PIN",
        "money got debited instead of credited",
        "PIN daalte hi paise chale gaye",
        "पिन डालने को कहा",
    ],
    "investment-group": [
        "then asked bigger deposit to withdraw",
        "cannot withdraw anything now",
        "withdraw ke liye aur paise maange",
        "निकालने के लिए और पैसे मांगे",
    ],
    "courier-customs": [
        "asked to pay a fine to clear it",
        "threatened a case unless I pay",
        "fine bharne ko bola",
        "जुर्माना भरने को कहा",
    ],
    "job-offer": [
        "then asked a deposit for prepaid tasks",
        "asked 10000 to unlock earnings",
        "task ke liye deposit maanga",
        "डिपॉजिट मांगा",
    ],
    "lottery-prize": [
        "asked processing fee first",
        "wanted GST charges before release",
        "fee bharne ko bola",
        "टैक्स के पैसे मांगे",
    ],
    "loan-app-harassment": [
        "demanding double repayment",
        "calling my office too",
        "paise wapas do warna photo bhejenge",
        "दोगुना पैसा मांग रहे हैं",
    ],
    "electricity-disconnection": [
        "asked to call an officer number and install an app",
        "asked to pay through a link",
        "app download karwaya",
        "ऐप डाउनलोड करवाया",
    ],
    "fake-customer-care": [
        "asked me to install anydesk",
        "asked card number for refund",
        "screen share app download karwaya",
        "कार्ड नंबर मांगा",
    ],
    "otp-call": ["and asked for the OTP", "wanted the OTP to stop a transaction", "OTP maanga", "ओटीपी मांगा"],
    "sextortion": [
        "demanding money or they will share it",
        "asked 50000 to delete the video",
        "paise do warna video viral karenge",
        "पैसे मांग रहे हैं",
    ],
}
OUTCOMES = ["", "", "", "I disconnected.", "Lost 4000.", "Reported on 1930.", "Please be careful.",
            "Luckily I did not pay.", "बहुत डर गया था।", "Paise nahi gaye.", "My bank blocked the card.",
            "Went to the cyber cell next day."]  # fmt: skip

# What 40 friends of an angry customer write about a real bakery.
GRUDGE_NOTES = ["Stale bread, cheated us", "Rude owner, dont go", "worst bakery in the area",
                "overpriced cakes, fraud shop", "bekar service", "They gave expired cream", "avoid avoid",
                "cheaters!!", "very bad experience at this shop", "doodh wali cake kharab thi", ""]  # fmt: skip
# Held out: only seeds >= 9100 (the scoring seeds) use these, so the engine is never tuned on them.
GRUDGE_NOTES_HOLDOUT = ["Their pastries made my kid sick", "billing counter guy misbehaved with my mother",
                        "charged me twice for one cake and refused to return", "dirty kitchen, saw cockroach",
                        "never order birthday cake from here", "late delivery and melted cake", "pathetic",
                        "ye dukaan wale log ache nahi hai", "मिठाई बासी थी", "shopkeeper was arrogant, 1 star", "",
                        "poor hygiene and they lied about eggless", "they sold me old bread"]  # fmt: skip
# The smarter friend group: copies a scam story it found online, with small edits.
COPIED_SCAM_NOTES = [
    "This number called and asked OTP pretending to be bank",
    "this number called me asking OTP pretending to be from bank",
    "Called asking for OTP, pretending bank",
    "Number asked OTP saying they are from the bank",
]


@dataclass
class Expect:
    """What the PRD says a lookup on this identifier must return."""

    kind: str  # genuine-known | low-report | unreported | attack | verified | challenged
    scenario: str
    id_type: str
    raw: str  # how the reports typed it
    canonical: str  # PRD normal form, worked out by hand from Appendix A rule 3
    variants: list[str] = field(default_factory=list)
    reporters: int = 0  # distinct genuine people behind it
    attack_detail: str = ""


@dataclass
class World:
    seed: int
    now: datetime
    reports: list[dict[str, Any]] = field(default_factory=list)
    expects: list[Expect] = field(default_factory=list)
    challenges: list[dict[str, Any]] = field(default_factory=list)
    areas: dict[str, str] = field(default_factory=dict)  # role -> pincode
    attack_areas: list[str] = field(default_factory=list)
    new_type: str = ""
    fake_new_type: str = ""


class Gen:
    def __init__(self, seed: int, now: datetime) -> None:
        self.r = random.Random(seed)
        self.now = now
        self.n = 0
        self.used: set[str] = set()
        # Mobile carriers put thousands of people behind one /24 (CGNAT). 120 shared prefixes for
        # ~700 genuine people means many honest strangers share a prefix.
        self.isp = [f"{self.r.choice([49, 103, 106, 117, 152, 157, 223])}.{self.r.randint(0, 255)}."
                    f"{self.r.randint(0, 255)}" for _ in range(120)]  # fmt: skip

    # -- identities
    def person(self) -> tuple[str, str]:
        rid = "r_" + "".join(self.r.choices("0123456789abcdef", k=8))
        return rid, self.r.choice(self.isp)

    def mobile(self) -> tuple[str, str, list[str]]:
        while True:
            d = str(self.r.choice([6, 7, 8, 9])) + "".join(self.r.choices(string.digits, k=9))
            if d not in self.used and len(set(d)) >= 4:
                self.used.add(d)
                break
        canon = "+91" + d
        variants = [f"+91 {d[:5]} {d[5:]}", "0" + d, f"{d[:5]}-{d[5:]}", "91" + d, d, canon]
        return self.r.choice(variants), canon, variants

    def upi(self) -> tuple[str, str, list[str]]:
        h = "".join(self.r.choices(string.ascii_lowercase, k=self.r.randint(5, 9))) + str(
            self.r.randint(1, 99)
        )
        bank = self.r.choice(["okaxis", "ybl", "paytm", "oksbi", "ibl"])
        canon = f"{h}@{bank}"
        variants = [canon, canon.upper(), f"{h.capitalize()}@{bank.upper()}", f" {canon} "]
        return self.r.choice(variants), canon, variants

    def url(self) -> tuple[str, str, list[str]]:
        stem = self.r.choice(["sbi-kyc", "hdfc-update", "icici-rewards", "bescom-bill", "india-post-track",
                              "kyc-verify", "refund-portal", "tax-refund-in"])  # fmt: skip
        dom = f"{stem}{self.r.randint(10, 999)}.{self.r.choice(['in', 'com', 'online', 'xyz'])}"
        path = self.r.choice(["/pay", "/login", "/update", "/kyc/step1"])
        canon = f"https://{dom}{path}"
        variants = [
            canon,
            f"http://www.{dom}{path}?utm=sms",
            f"https://www.{dom}{path}/",
            f"http://{dom}{path}",
        ]
        return self.r.choice(variants), canon, variants

    def sender(self) -> tuple[str, str, list[str]]:
        while True:
            code = "".join(self.r.choices(string.ascii_uppercase, k=6))
            if code not in {v for t, v in VERIFIED if t == "sender_id"} and code not in self.used:
                self.used.add(code)
                break
        variants = [code, f"VM-{code}", f"AD-{code}", f"JD-{code}"]
        return self.r.choice(variants), code, variants

    def ident(
        self, kinds: tuple[str, ...] = ("phone", "phone", "phone", "upi", "url", "sender_id")
    ) -> tuple[str, str, str, list[str]]:
        t = self.r.choice(kinds)
        raw, canon, var = {"phone": self.mobile, "upi": self.upi, "url": self.url, "sender_id": self.sender}[
            t
        ]()
        return t, raw, canon, var

    # -- one report
    def report(self, *, who: tuple[str, str], id_type: str, value: str, pincode: str, scam_type: str,
               occurred: datetime, lag: timedelta, note: str, channel: str | None = None) -> dict[str, Any]:  # fmt: skip
        self.n += 1
        loc, city, _, _ = AREAS[pincode]
        reported = min(occurred + lag, self.now)
        return {
            "report_id": f"rep_j{self.n:06d}",
            "occurred_at": occurred.astimezone(IST).isoformat(timespec="seconds"),
            "reported_at": reported.astimezone(IST).isoformat(timespec="seconds"),
            "reporter_id": who[0],
            "ip_prefix": who[1],
            "channel": channel or self.r.choice(TYPE_CHANNELS.get(scam_type, ["Something else"])),
            "scam_type": scam_type,
            "identifier_type": id_type,
            "identifier_value": value,
            "pincode": pincode,
            "locality": loc,
            "city": city,
            "note": note,
            "has_screenshot": self.r.random() < 0.3,
            "amount_lost_inr": self.r.choice([0, 0, 0, 500, 2000, 15000, 98000]),
        }

    def victim_note(self, scam_type: str) -> str:
        if self.r.random() < 0.25:  # a quarter of real victims leave the note empty
            return ""
        st = scam_type if scam_type in CLAIMS else "otp-call"
        parts = [self.r.choice(OPENERS), self.r.choice(CLAIMS[st])]
        if self.r.random() < 0.8:
            parts.append(self.r.choice(DEMANDS[st]))
        parts.append(self.r.choice(OUTCOMES))
        return " ".join(p for p in parts if p)

    def lag(self, fast: bool = False) -> timedelta:
        if fast:
            return timedelta(minutes=self.r.uniform(1, 40))
        return timedelta(
            minutes=self.r.choice([5, 20, 45, 90, 240, 600, 1440, 2880]) * self.r.uniform(0.5, 1.5)
        )

    def ago(self, lo_h: float, hi_h: float) -> datetime:
        return self.now - timedelta(hours=self.r.uniform(lo_h, hi_h))


def build(seed: int, now: datetime | None = None) -> World:
    now = now or datetime.now(IST)
    g = Gen(seed, now)
    r = g.r
    w = World(seed=seed, now=now)

    pins = list(AREAS)
    r.shuffle(pins)
    for role in ("spike", "normal", "new_type", "old", "fake_alert"):
        w.areas[role] = pins.pop()
    w.attack_areas = [pins.pop() for _ in range(3)]
    open_areas = pins  # 17 areas for everyday genuine traffic

    # ---------- Row 2: real scams, reported by k independent people over days
    for k in [3, 3, 4, 4, 5, 6, 7, 8, 10, 12, 15, 20] + [r.randint(3, 15) for _ in range(8)]:
        t, raw, canon, var = g.ident()
        st = r.choice(TYPES)
        home = r.sample(open_areas, r.randint(1, 3))
        wave = r.random() < 0.25  # a viral wave: everyone reports within ~2 hours of the same call
        start = r.uniform(2, 20 * 24)
        for _ in range(k):
            occ = g.ago(start - 2, start) if wave else g.ago(1, start)
            g_type = st if r.random() < 0.85 else r.choice(TYPES)  # victims sometimes mislabel
            w.reports.append(g.report(who=g.person(), id_type=t, value=r.choice(var), pincode=r.choice(home),
                                      scam_type=g_type, occurred=occ, lag=g.lag(fast=wave),
                                      note=g.victim_note(st)))  # fmt: skip
        w.expects.append(
            Expect("genuine-known", f"genuine-k{k}{'-wave' if wave else ''}", t, raw, canon, var, k)
        )

    # ---------- Low-report numbers: 1 or 2 genuine people
    for _ in range(16):
        t, raw, canon, var = g.ident()
        k = r.choice([1, 1, 2])
        st = r.choice(TYPES)
        pin = r.choice(open_areas)
        for _ in range(k):
            w.reports.append(g.report(who=g.person(), id_type=t, value=r.choice(var), pincode=pin, scam_type=st,
                                      occurred=g.ago(1, 200), lag=g.lag(), note=g.victim_note(st)))  # fmt: skip
        w.expects.append(Expect("low-report", f"low-k{k}", t, raw, canon, var, k))

    # ---------- Unreported: valid, never reported
    for _ in range(20):
        t, raw, canon, var = g.ident()
        w.expects.append(Expect("unreported", "unreported", t, raw, canon, var))

    # ---------- Row 1 tricks, at and around the brief's sizes, in attack-only areas
    def bakery() -> tuple[str, str, list[str]]:
        d = "80" + "".join(r.choices(string.digits, k=8))  # a Bengaluru landline like the brief's bakery
        g.used.add(d)
        return f"+91 80 {d[2:6]} {d[6:]}", "+91" + d, [f"+91 80 {d[2:6]} {d[6:]}", "0" + d, "91" + d]

    for size, style in [(40, "grudge"), (r.randint(30, 60), "grudge"), (40, "copied-scam"), (40, "blank"),
                        (r.randint(25, 45), "mixed")]:  # fmt: skip
        raw, canon, var = bakery()
        pin = r.choice(w.attack_areas)
        span_h = r.choice([3, 12, 48, 120])
        ips = r.sample(g.isp, r.randint(6, 30))  # friends at home, on many different connections
        for _ in range(size):
            grudge = GRUDGE_NOTES_HOLDOUT if seed >= 9100 else GRUDGE_NOTES
            note = {"grudge": r.choice(grudge), "copied-scam": r.choice(COPIED_SCAM_NOTES), "blank": "",
                    "mixed": r.choice(grudge + COPIED_SCAM_NOTES + [""])}[style]  # fmt: skip
            st = r.choice(["otp-call", "fake-customer-care", "other", "lottery-prize"])
            rid = "r_" + "".join(r.choices("0123456789abcdef", k=8))
            w.reports.append(g.report(who=(rid, r.choice(ips)), id_type="phone", value=r.choice(var), pincode=pin,
                                      scam_type=st, occurred=g.ago(0.5, span_h), lag=g.lag(fast=True),
                                      note=note))  # fmt: skip
        w.expects.append(Expect("attack", f"friends-{style}", "phone", raw, canon, var,
                                attack_detail=f"{size} friends, {len(ips)} /24s, {span_h}h, notes={style}"))  # fmt: skip

    for size in [22, r.randint(12, 30), r.randint(12, 30)]:
        t, raw, canon, var = g.ident()
        ip = r.choice(g.isp)  # one Wi-Fi, and that prefix is also shared by honest strangers
        pin = r.choice(w.attack_areas)
        st = r.choice(TYPES)
        span_h = r.choice([1, 6, 30])
        for _ in range(size):
            rid = "r_" + "".join(r.choices("0123456789abcdef", k=8))
            w.reports.append(g.report(who=(rid, ip), id_type=t, value=r.choice(var), pincode=pin, scam_type=st,
                                      occurred=g.ago(0.3, span_h), lag=g.lag(fast=True),
                                      note=g.victim_note(st)))  # fmt: skip
        w.expects.append(Expect("attack", f"sybil-{size}", t, raw, canon, var,
                                attack_detail=f"{size} accounts on {ip}, {span_h}h, victim-style notes"))  # fmt: skip

    for times in [6, r.randint(4, 10)]:
        t, raw, canon, var = g.ident()
        who = g.person()
        pin = r.choice(w.attack_areas)
        st = r.choice(TYPES)
        for _ in range(times):
            w.reports.append(g.report(who=who, id_type=t, value=r.choice(var), pincode=pin, scam_type=st,
                                      occurred=g.ago(0.5, 200), lag=g.lag(), note=g.victim_note(st)))  # fmt: skip
        w.expects.append(Expect("attack", f"spam-{times}x", t, raw, canon, var, reporters=1,
                                attack_detail=f"one reporter, {times} reports"))  # fmt: skip

    # ---------- Verified entries bombed by many genuine-looking people
    for t, v in r.sample(VERIFIED, 4):
        st = "fake-customer-care"
        pin = r.choice(open_areas)
        for _ in range(r.randint(8, 15)):
            w.reports.append(g.report(who=g.person(), id_type=t, value=v, pincode=pin, scam_type=st,
                                      occurred=g.ago(1, 100), lag=g.lag(), note=g.victim_note(st)))  # fmt: skip
    for t, v in VERIFIED:
        w.expects.append(Expect("verified", "verified", t, v, ""))

    # ---------- Bonus: a challenged number with real reports behind it
    t, raw, canon, var = g.ident(("phone",))
    st = r.choice(TYPES)
    for _ in range(8):
        w.reports.append(g.report(who=g.person(), id_type=t, value=r.choice(var), pincode=r.choice(open_areas),
                                  scam_type=st, occurred=g.ago(2, 100), lag=g.lag(), note=g.victim_note(st)))  # fmt: skip
    w.challenges.append({"identifier_type": t, "identifier_value": raw, "claimant_name": "Sharma Sweets",
                         "contact_email": "owner@example.com", "proof_note": "GST certificate attached."})  # fmt: skip
    w.expects.append(Expect("challenged", "challenged", t, raw, canon, var, 8))

    # ---------- Row 3: areas with a known alert answer. Each genuine report is a fresh number.
    def steady(pin: str, per_day: float, days: tuple[float, float], types: list[str]) -> None:
        n = round(per_day * (days[1] - days[0]))
        for _ in range(n):
            st = r.choice(types)
            t2, _, _, var2 = g.ident()
            w.reports.append(g.report(who=g.person(), id_type=t2, value=r.choice(var2), pincode=pin,
                                      scam_type=st, occurred=g.ago(days[0] * 24, days[1] * 24), lag=g.lag(),
                                      note=g.victim_note(st)))  # fmt: skip

    local_types = r.sample(TYPES, 3)
    base = r.choice([1.0, 2.0, 3.0])
    steady(w.areas["spike"], base, (1.05, 8), local_types)
    spike_n = max(5, int(2 * base)) + r.randint(2, 6)
    steady(w.areas["spike"], spike_n, (0.02, 0.95), local_types)

    steady(w.areas["normal"], base + 1, (1.05, 8), local_types)
    steady(w.areas["normal"], base + 1, (0.02, 0.95), local_types)

    old_types = r.sample(TYPES, 3)
    w.new_type = r.choice([t for t in TYPES if t not in old_types])
    steady(w.areas["new_type"], 0.5, (1.05, 29), old_types)
    steady(w.areas["new_type"], r.choice([1.0, 2.0]), (0.05, 0.95), [w.new_type])

    steady(w.areas["old"], 0.7, (9, 40), r.sample(TYPES, 4))

    # Fake alert bait: a quiet area, then 22 sybils on one /24 and a 6x spammer with a brand-new type.
    fa = w.areas["fake_alert"]
    fa_types = r.sample(TYPES, 2)
    steady(fa, 1.0, (1.05, 29), fa_types)
    t, raw, canon, var = g.ident()
    ip = r.choice(g.isp)
    for _ in range(22):
        rid = "r_" + "".join(r.choices("0123456789abcdef", k=8))
        w.reports.append(g.report(who=(rid, ip), id_type=t, value=r.choice(var), pincode=fa, scam_type=fa_types[0],
                                  occurred=g.ago(0.2, 6), lag=g.lag(fast=True), note=g.victim_note(fa_types[0])))  # fmt: skip
    w.fake_new_type = r.choice([x for x in TYPES if x not in fa_types])
    t, raw, canon, var = g.ident()
    who = g.person()
    for _ in range(6):
        w.reports.append(g.report(who=who, id_type=t, value=r.choice(var), pincode=fa, scam_type=w.fake_new_type,
                                  occurred=g.ago(0.2, 20), lag=g.lag(fast=True),
                                  note=g.victim_note(w.fake_new_type)))  # fmt: skip

    w.reports.sort(key=lambda x: x["reported_at"])
    return w


# Values that can never be valid, from Appendix A ("A value that cannot be valid, like 12345, is 400").
JUNK_LOOKUPS = [("phone", "12345"), ("phone", "abc"), ("phone", ""), ("phone", "+91 12345"), ("phone", "0000000000"),
                ("phone", "1234567890123456"), ("upi", "no-at-sign"), ("upi", "@okaxis"), ("url", "not a url"),
                ("url", "ftp://x"), ("sender_id", "HD"), ("sender_id", "12-34"), ("email", "a@b.com")]  # fmt: skip
