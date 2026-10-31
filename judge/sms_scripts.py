"""Scam SMS scripts as they circulate in India, with the parts that change between sends.

Used to measure the wording search (tests/test_explore.py) and to seed a demo campaign where one
script moves across several numbers. Written for this project from the public patterns reported
by banks, DoT and I4C advisories; no real message, number or name.
"""

import random

SCRIPTS: dict[str, tuple[str, str]] = {
    "electricity": (
        "electricity-disconnection",
        "Dear consumer your electricity power will be disconnected tonight at {time} because your previous "
        "month bill was not updated. Please immediately call our electricity officer {name} on {num}. Thank you",
    ),
    "kyc": (
        "fake-kyc-link",
        "Dear {bank} customer, your account will be blocked today. Please update your PAN card KYC by "
        "clicking {link} or call {num}. Ignore if already done.",
    ),
    "parcel": (
        "courier-customs",
        "FedEx: your parcel from {city} has been held at customs because it contains illegal items. "
        "Press 1 or call {num} immediately to avoid a police case. Ref {ref}",
    ),
    "lottery": (
        "lottery-prize",
        "Congratulations! Your number has won Rs {amt} in the KBC lucky draw. To claim your prize "
        "contact our manager {name} on WhatsApp {num} and pay the processing fee.",
    ),
    "job": (
        "job-offer",
        "Hello, we are hiring part time staff. Earn Rs {amt} daily by liking YouTube videos from home. "
        "No fees. Contact HR {name} on Telegram or WhatsApp {num}.",
    ),
    "arrest": (
        "digital-arrest",
        "This is a notice from CBI cyber cell. An FIR is registered against your Aadhaar for money laundering. "
        "Join the video call with officer {name} on {num} within 2 hours or an arrest warrant will be issued.",
    ),
}

_NAMES = ["Rakesh Kumar", "Amit Sharma", "S K Verma", "Pooja Singh", "Manoj", "R Gupta", "Vikram"]
_BANKS = ["SBI", "HDFC", "ICICI", "Axis", "PNB"]
_CITIES = ["Mumbai", "Delhi", "Taiwan", "Dubai", "Hong Kong"]


def fill(script: str, r: random.Random, num: str | None = None) -> str:
    """One send of a script: new number, name, amount and so on, plus the small edits forwards pick up."""
    text = SCRIPTS[script][1].format(
        num=num or f"{r.choice('6789')}{r.randrange(10**8, 10**9)}",
        name=r.choice(_NAMES),
        bank=r.choice(_BANKS),
        city=r.choice(_CITIES),
        link=f"{r.choice(['sbi', 'kyc', 'bank'])}-{r.choice(['update', 'verify', 'help'])}{r.randrange(10, 99)}.in",
        amt=f"{r.choice([25, 35, 50])},{r.choice(['000', '500'])}",
        time=f"{r.choice([9, 9, 10])}.{r.choice(['30', '00'])} pm",
        ref=f"FX{r.randrange(10**5, 10**6)}",
    )
    words = text.split()
    if r.random() < 0.5:  # a forward drops or doubles a word
        i = r.randrange(len(words))
        words.pop(i) if r.random() < 0.5 else words.insert(i, words[i])
    if r.random() < 0.3:
        words.insert(0, r.choice(["Fwd:", "Dear Sir,", "URGENT"]))
    text = " ".join(words)
    return text.upper() if r.random() < 0.15 else text
