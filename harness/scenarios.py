"""Randomised attack and genuine-campaign generators (MASTER_PLAN section 6).

Every seed draws fresh identifiers, sizes, timings, areas and notes, so the trust rules cannot be
tuned to one dataset (the judges use a secret one). Each scenario carries its own expectation.
"""

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any

from app.domain.areas import AREAS
from app.domain.catalog import CHANNELS, SCAM_TYPES

Report = dict[str, Any]

_OPEN = [
    "Got a call",
    "Received a video call",
    "Someone called me",
    "Mujhe call aaya",
    "मुझे कॉल आया",
    "My father got a call",
    "A man phoned my mother",
    "WhatsApp call came",
    "Aaj subah call aaya",
]
_WHO = [
    "from a man in police uniform",
    "claiming to be from customs",
    "saying he is from the bank",
    "from fake CBI officer",
    "पुलिस वाला बनकर",
    "claiming my parcel had drugs",
    "saying KYC is pending",
    "from so called electricity office",
    "offering part time job",
]
_ASK = [
    "asked me to pay a fine",
    "wanted OTP",
    "told me to scan a QR code",
    "demanded money to avoid arrest",
    "पैसे मांगे",
    "asked for card details",
    "said account will be blocked",
    "asked deposit for task",
    "bola paise transfer karo",
]
_END = [
    "I lost money",
    "I disconnected",
    "my uncle also got same call",
    "bahut dar gaya tha",
    "मैंने फोन काट दिया",
    "reported to 1930",
    "very scary",
    "please be careful",
    "it went on for hours",
]
_SHORT = [
    "fake police call",
    "asked otp",
    "fraud call",
    "kyc call fake",
    "scam call aaya",
    "paise mange",
    "qr scan bola",
    "fake courier",
    "loan threat",
    "job deposit",
    "bank wala fake",
    "बिजली कट कॉल",
]
_INSULT = [
    "bad shop",
    "dont buy here",
    "worst",
    "cheaters",
    "avoid",
    "fraud shop",
    "bekar",
    "very bad bakery",
]


def _ip(rng: random.Random) -> str:
    return f"{rng.randint(1, 223)}.{rng.randint(0, 255)}.{rng.randint(0, 255)}"


def _phone(rng: random.Random) -> str:
    digits = str(rng.choice("6789")) + "".join(rng.choice("0123456789") for _ in range(9))
    style = rng.randrange(4)
    if style == 0:
        return f"+91 {digits[:5]} {digits[5:]}"
    if style == 1:
        return "0" + digits
    if style == 2:
        return f"{digits[:5]}-{digits[5:]}"
    return "91" + digits


def _note(rng: random.Random) -> str:
    parts = [rng.choice(_OPEN), rng.choice(_WHO), rng.choice(_ASK), rng.choice(_END)]
    if rng.random() < 0.5:
        parts.append(f"around {rng.randint(1, 12)} {rng.choice(['am', 'pm'])}")
    if rng.random() < 0.4:
        parts.append(f"Rs {rng.randint(2, 500) * 100}")
    return " ".join(parts)


@dataclass
class Scenario:
    name: str
    kind: str  # "genuine" or "attack"
    identifier_type: str
    identifier_value: str
    reports: list[Report]
    expect: Callable[[dict[str, Any]], str | None]  # returns a failure message or None
    soft: bool = False  # a known limit we measure and disclose, not a hard requirement
    extra_ids: list[str] = field(default_factory=list)


class Builder:
    def __init__(self, seed: int, now: datetime) -> None:
        self.rng = random.Random(seed)
        self.now = now
        self.seed = seed
        self._n = 0

    def _id(self, prefix: str) -> str:
        self._n += 1
        return f"{prefix}_{self.seed}_{self._n}_{self.rng.randrange(16**6):06x}"

    def report(
        self,
        value: str,
        *,
        occurred: datetime,
        delay_min: float,
        reporter: str | None = None,
        ip: str | None = None,
        pincode: str | None = None,
        note: str = "",
        scam_type: str = "digital-arrest",
        id_type: str = "phone",
        screenshot: bool = False,
        amount: int = 0,
    ) -> Report:
        area = next((a for a in AREAS if a.pincode == pincode), None) or self.rng.choice(AREAS)
        return {
            "report_id": self._id("rep"),
            "occurred_at": occurred.isoformat(timespec="seconds"),
            "reported_at": (occurred + timedelta(minutes=delay_min)).isoformat(timespec="seconds"),
            "reporter_id": reporter or self._id("r"),
            "ip_prefix": ip or _ip(self.rng),
            "channel": "Phone call" if id_type == "phone" else self.rng.choice(CHANNELS),
            "scam_type": scam_type,
            "identifier_type": id_type,
            "identifier_value": value,
            "pincode": area.pincode,
            "locality": area.locality,
            "city": area.city,
            "note": note,
            "has_screenshot": screenshot,
            "amount_lost_inr": amount,
        }

    def _times(self, n: int, span: timedelta, end_ago: timedelta = timedelta(minutes=30)) -> list[datetime]:
        end = self.now - end_ago
        return sorted(end - span * self.rng.random() for _ in range(n))

    # ---------------- genuine campaigns: must become KNOWN_SCAM ----------------
    def genuine(
        self,
        name: str,
        n: int,
        span: timedelta,
        *,
        rich: bool,
        areas: int = 25,
        ip_pool: int | None = None,
        quick: bool = False,
    ) -> Scenario:
        value = _phone(self.rng)
        scam = self.rng.choice(SCAM_TYPES)
        pins = [a.pincode for a in self.rng.sample(AREAS, min(areas, len(AREAS)))]
        pool = [_ip(self.rng) for _ in range(ip_pool)] if ip_pool else None
        reports = []
        for t in self._times(n, span):
            reports.append(
                self.report(
                    value,
                    occurred=t,
                    delay_min=self.rng.uniform(1, 20) if quick else self.rng.uniform(5, 600),
                    ip=self.rng.choice(pool) if pool else None,
                    pincode=self.rng.choice(pins),
                    note=_note(self.rng) if rich else self.rng.choice(_SHORT) + f" {self.rng.randint(1, 99)}",
                    scam_type=scam,
                    screenshot=rich and self.rng.random() < 0.4,
                    amount=self.rng.randint(1, 200) * 500 if rich and self.rng.random() < 0.5 else 0,
                )
            )
        return Scenario(name, "genuine", "phone", value, reports, _expect_known)

    # ---------------- attacks: must never become KNOWN_SCAM ----------------
    def bombing(self, name: str, notes: str, n: int = 40) -> Scenario:
        value = _phone(self.rng)
        pins = [a.pincode for a in self.rng.sample(AREAS[:15], 2)]
        ips = [_ip(self.rng) for _ in range(15)]
        base = self.now - timedelta(hours=self.rng.uniform(1, 48))
        template = self.rng.choice(_INSULT) + " fraud bakery, they cheated me"
        reports = []
        for i in range(n):
            if notes == "blank":
                note = ""
            elif notes == "copy":
                note = template + ("!" * self.rng.randint(0, 2))
            elif notes == "template":
                note = f"{self.rng.choice(_INSULT)} {template}"
            else:  # unique short insults
                note = " ".join(self.rng.sample(_INSULT, 2)) + f" {i}"
            t = base + timedelta(minutes=self.rng.uniform(0, 20))
            reports.append(
                self.report(
                    value,
                    occurred=t,
                    delay_min=self.rng.uniform(0, 2),
                    ip=self.rng.choice(ips),
                    pincode=self.rng.choice(pins),
                    note=note,
                    scam_type=self.rng.choice(SCAM_TYPES),
                )
            )
        return Scenario(name, "attack", "phone", value, reports, _expect_not_known_masked)

    def bombing_slow_blank(self, n: int = 40) -> Scenario:
        """Friends on their own networks, no notes, spread over a day so no burst rule fires."""
        value = _phone(self.rng)
        pins = [a.pincode for a in self.rng.sample(AREAS[:15], 3)]
        reports = [
            self.report(value, occurred=t, delay_min=self.rng.uniform(1, 30), pincode=self.rng.choice(pins))
            for t in self._times(n, timedelta(hours=24))
        ]
        return Scenario(
            "bombing-40-blank-over-a-day", "attack", "phone", value, reports, _expect_not_known_masked
        )

    def sybil(self, n: int = 22) -> Scenario:
        value = _phone(self.rng)
        ip = _ip(self.rng)
        pin = self.rng.choice(AREAS).pincode
        base = self.now - timedelta(hours=self.rng.uniform(1, 48))
        reports = [
            self.report(
                value,
                occurred=base + timedelta(minutes=self.rng.uniform(0, 15)),
                delay_min=1,
                ip=ip,
                pincode=pin,
                note=_note(self.rng),
            )
            for _ in range(n)
        ]
        return Scenario("sybil-22-one-wifi", "attack", "phone", value, reports, _expect_one_person)

    def slow_drip(self, n: int = 20) -> Scenario:
        value = _phone(self.rng)
        ips = [_ip(self.rng) for _ in range(2)]
        reports = [
            self.report(
                value,
                occurred=t,
                delay_min=self.rng.uniform(5, 60),
                ip=self.rng.choice(ips),
                note=_note(self.rng),
            )
            for t in self._times(n, timedelta(days=10))
        ]
        return Scenario(
            "slow-drip-sybil-10-days", "attack", "phone", value, reports, _expect_not_known_masked
        )

    def spammer(self, times: int = 6) -> Scenario:
        value = _phone(self.rng)
        reporter, ip = self._id("r"), _ip(self.rng)
        base = self.now - timedelta(hours=self.rng.uniform(2, 48))
        reports = [
            self.report(
                value, occurred=base, delay_min=i * 9 + 1, reporter=reporter, ip=ip, note=_note(self.rng)
            )
            for i in range(times)
        ]
        return Scenario("spam-6x-one-person", "attack", "phone", value, reports, _expect_one_person)

    def verified_attack(self, value: str, id_type: str, n: int = 50) -> Scenario:
        reports = [
            self.report(
                value,
                occurred=t,
                delay_min=self.rng.uniform(5, 300),
                note=_note(self.rng),
                id_type=id_type,
                screenshot=True,
                amount=5000,
            )
            for t in self._times(n, timedelta(days=5))
        ]
        return Scenario(f"bomb-verified-{value}", "attack", id_type, value, reports, _expect_verified)

    def llm_brigade(self, name: str, *, instant: bool, uniform: bool, n: int = 20) -> Scenario:
        """Distinct people and networks, unique fluent notes, one scam type, all inside 30 minutes.

        `instant`: each filed within a minute of the invented incident. `uniform`: note lengths
        as even as a batch of generated text. Real victims rarely do either, and never both at scale.
        """
        value = _phone(self.rng)
        base = self.now - timedelta(hours=self.rng.uniform(1, 24))
        width = self.rng.randint(70, 110)
        reports = []
        for _ in range(n):
            note = _note(self.rng)
            if uniform:
                note = (note + " " + _note(self.rng))[: width + self.rng.randint(-4, 4)]
            reports.append(
                self.report(
                    value,
                    occurred=base + timedelta(minutes=self.rng.uniform(0, 30)),
                    delay_min=self.rng.uniform(0.1, 1.0) if instant else self.rng.uniform(3, 45),
                    note=note,
                )
            )
        return Scenario(name, "attack", "phone", value, reports, _expect_not_known_masked)

    def genuine_viral_wave(self, n: int = 25) -> Scenario:
        """A real wave: many victims within 90 minutes, own words, no screenshots, reported minutes later."""
        value = _phone(self.rng)
        base = self.now - timedelta(hours=self.rng.uniform(2, 20))
        reports = [
            self.report(
                value,
                occurred=base + timedelta(minutes=self.rng.uniform(0, 90)),
                delay_min=self.rng.uniform(2, 60),
                note=_note(self.rng),
            )
            for _ in range(n)
        ]
        return Scenario("genuine-viral-wave-90min", "genuine", "phone", value, reports, _expect_known)

    def genuine_zero_lag(self, n: int = 10) -> Scenario:
        """A lazy dataset where reported_at always equals occurred_at; timing must not be held against it."""
        value = _phone(self.rng)
        reports = [
            self.report(value, occurred=t, delay_min=0, note=_note(self.rng))
            for t in self._times(n, timedelta(hours=self.rng.uniform(2, 30)))
        ]
        return Scenario("genuine-zero-lag-dataset", "genuine", "phone", value, reports, _expect_known)


def _expect_known(body: dict[str, Any]) -> str | None:
    if body.get("verdict") != "KNOWN_SCAM":
        return f"expected KNOWN_SCAM, got {body.get('verdict')}"
    if "X" in str(body.get("display_value")):
        return "a confirmed scam should be unmasked"
    return None


def _expect_not_known(body: dict[str, Any]) -> str | None:
    return "fake reports made it KNOWN_SCAM" if body.get("verdict") == "KNOWN_SCAM" else None


def _expect_not_known_masked(body: dict[str, Any]) -> str | None:
    if msg := _expect_not_known(body):
        return msg
    if body.get("identifier_type", "phone") == "phone" and "X" not in str(body.get("display_value")):
        return "number unmasked by fake reports"
    return None


def _expect_one_person(body: dict[str, Any]) -> str | None:
    if msg := _expect_not_known_masked(body):
        return msg
    if body.get("distinct_reporters") != 1:
        return f"expected distinct_reporters 1, got {body.get('distinct_reporters')}"
    return None


def _expect_verified(body: dict[str, Any]) -> str | None:
    v = body.get("verdict")
    return None if v == "VERIFIED_BUSINESS" else f"expected VERIFIED_BUSINESS, got {v}"


JUNK: list[tuple[str, str]] = [
    ("phone", "12345"),
    ("phone", "test"),
    ("phone", ""),
    ("phone", "9999999999"),
    ("upi", "test"),
    ("url", "test"),
    ("url", "12345"),
    ("sender_id", "12345"),
    ("sender_id", "test"),
]

VERIFIED_SAMPLES: list[tuple[str, str]] = [
    ("phone", "1930"),
    ("phone", "1800 1600"),
    ("phone", "+91 80 4100 2233"),
    ("sender_id", "VM-HDFCBK"),
    ("url", "https://cybercrime.gov.in"),
    ("upi", "freshbakes@okaxis"),
]


def trust_suite(seed: int, now: datetime) -> list[Scenario]:
    b = Builder(seed, now)
    rng = b.rng
    suite = [
        b.genuine("genuine-rich", rng.randint(8, 25), timedelta(days=rng.uniform(1, 6)), rich=True),
        b.genuine(
            "genuine-plain",
            rng.randint(6, 12),
            timedelta(hours=rng.uniform(3, 30)),
            rich=False,
            areas=3,
            quick=True,
        ),
        b.genuine("genuine-small", 5, timedelta(hours=rng.uniform(4, 48)), rich=rng.random() < 0.5),
        b.genuine("genuine-local-one-area", rng.randint(8, 15), timedelta(days=2), rich=False, areas=1),
        b.genuine("genuine-ip-pool-collisions", 25, timedelta(days=3), rich=True, ip_pool=30),
        b.bombing("bombing-40-blank-notes", "blank"),
        b.bombing("bombing-40-copy-paste", "copy"),
        b.bombing("bombing-40-template", "template"),
        b.bombing("bombing-40-unique-short", "unique-short"),
        b.bombing_slow_blank(),
        b.sybil(),
        b.slow_drip(),
        b.spammer(),
        b.genuine_viral_wave(),
        b.genuine_zero_lag(),
        b.llm_brigade("llm-brigade-instant", instant=True, uniform=False),
        b.llm_brigade("llm-brigade-uniform-length", instant=False, uniform=True),
    ]
    for id_type, value in VERIFIED_SAMPLES:
        suite.append(b.verified_attack(value, id_type, n=12))
    return suite
