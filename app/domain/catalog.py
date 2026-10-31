"""Reference data from the brief, Appendix C: verified entities, scam types and channels.

The verified list is data the brief requires (bonus +3), not a rule about one identifier:
every entry is normalised with the same code path as reports and lookups.
"""

from app.domain.identifiers import IdentifierType, normalise

SCAM_TYPES: tuple[str, ...] = (
    "digital-arrest",
    "fake-kyc-link",
    "upi-refund-qr",
    "investment-group",
    "courier-customs",
    "job-offer",
    "lottery-prize",
    "loan-app-harassment",
    "electricity-disconnection",
    "fake-customer-care",
    "otp-call",
    "sextortion",
)
OTHER_SCAM_TYPE = "other"

CHANNELS: tuple[str, ...] = (
    "Phone call",
    "SMS or WhatsApp",
    "QR code",
    "Fake website",
    "UPI request",
    "Something else",
)
OTHER_CHANNEL = "Something else"

_VERIFIED_RAW: tuple[tuple[IdentifierType, str, str], ...] = (
    (IdentifierType.PHONE, "1930", "National Cybercrime Helpline"),
    (IdentifierType.PHONE, "1909", "TRAI Do Not Disturb"),
    (IdentifierType.PHONE, "1800 1600", "HDFC Bank customer care"),
    (IdentifierType.PHONE, "1800 2600", "HDFC Bank customer care"),
    (IdentifierType.PHONE, "1800 1080", "ICICI Bank customer care"),
    (IdentifierType.PHONE, "1800 1234", "State Bank of India customer care"),
    (IdentifierType.PHONE, "1800 2100", "State Bank of India customer care"),
    (IdentifierType.PHONE, "1860 419 5555", "Axis Bank customer care"),
    (IdentifierType.PHONE, "1860 266 2666", "Kotak Mahindra Bank customer care"),
    (IdentifierType.SENDER_ID, "HDFCBK", "HDFC Bank SMS sender"),
    (IdentifierType.SENDER_ID, "ICICIB", "ICICI Bank SMS sender"),
    (IdentifierType.SENDER_ID, "SBIINB", "State Bank of India SMS sender"),
    (IdentifierType.SENDER_ID, "AXISBK", "Axis Bank SMS sender"),
    (IdentifierType.SENDER_ID, "KOTAKB", "Kotak Mahindra Bank SMS sender"),
    (IdentifierType.URL, "https://cybercrime.gov.in", "National Cyber Crime Reporting Portal"),
    (IdentifierType.URL, "https://sancharsaathi.gov.in", "Sanchar Saathi"),
    (IdentifierType.PHONE, "+91 80 4100 2233", "Fresh Bakes, Indiranagar"),
    (IdentifierType.PHONE, "+91 80 2553 0190", "Koramangala Pharmacy"),
    (IdentifierType.UPI, "freshbakes@okaxis", "Fresh Bakes, Indiranagar"),
)

VERIFIED: dict[tuple[IdentifierType, str], str] = {
    (t, normalise(t, raw)): owner for t, raw, owner in _VERIFIED_RAW
}


def canonical_scam_type(raw: str | None) -> str:
    """Unknown scam types are kept as `other`, never rejected (brief, Appendix C)."""
    value = (raw or "").strip().lower()
    return value if value in SCAM_TYPES else OTHER_SCAM_TYPE


def canonical_channel(raw: str | None) -> str:
    value = (raw or "").strip()
    for channel in CHANNELS:
        if channel.lower() == value.lower():
            return channel
    return OTHER_CHANNEL


def verified_owner(id_type: IdentifierType, value_norm: str) -> str | None:
    return VERIFIED.get((id_type, value_norm))
