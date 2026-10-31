"""Every normalisation and masking example in the brief (Appendix A rule 3, A.3, Appendix C) is a test."""

import pytest

from app.domain.catalog import VERIFIED, canonical_channel, canonical_scam_type
from app.domain.identifiers import IdentifierType as T
from app.domain.identifiers import InvalidIdentifier, mask, normalise


@pytest.mark.parametrize(
    "raw",
    [
        "+91 98765 43210",
        "09876543210",
        "98765-43210",
        "919876543210",
        "9876543210",
        "(98765) 43210",
        "‪+91 98765 43210‬",
        "0091 98765 43210",
        "+91-98765-43210",
    ],
)
def test_phone_variants_are_one_number(raw: str) -> None:
    assert normalise(T.PHONE, raw) == "+919876543210"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1930", "1930"),
        ("1909", "1909"),
        ("1800 1600", "18001600"),
        ("1860 419 5555", "18604195555"),
        ("1860 266 2666", "18602662666"),
        ("+91 80 4100 2233", "+918041002233"),
        ("080 2553 0190", "+918025530190"),
        ("14440", "14440"),
    ],
)
def test_helplines_toll_free_and_landlines(raw: str, expected: str) -> None:
    assert normalise(T.PHONE, raw) == expected


@pytest.mark.parametrize(
    "raw",
    [
        "12345",
        "test",
        "",
        "   ",
        "9999999999",
        "0000000000",
        "98765",
        "+1 415 555 0100",
        "98765432101",
        "1234567890",
        "1234",
        "1111",
        "+91 98765 4321a",
    ],
)
def test_junk_phones_rejected(raw: str) -> None:
    with pytest.raises(InvalidIdentifier):
        normalise(T.PHONE, raw)


def test_upi() -> None:
    assert normalise(T.UPI, "Ravi12@OKAXIS") == "ravi12@okaxis"
    assert normalise(T.UPI, " ravi12 @okaxis ") == "ravi12@okaxis"
    assert normalise(T.UPI, "upi://pay?pa=Ravi12@okaxis&pn=Ravi&am=100") == "ravi12@okaxis"
    for junk in ("test", "12345", "a@b@c", "@okaxis", "ravi@", "ravi@123"):
        with pytest.raises(InvalidIdentifier):
            normalise(T.UPI, junk)


@pytest.mark.parametrize(
    "raw",
    [
        "http://www.sbi-kyc.in/pay?utm=sms",
        "https://sbi-kyc.in/pay",
        "sbi-kyc.in/pay/",
        "HTTPS://WWW.SBI-KYC.IN/pay#x",
        "https://sbi-kyc.in:443/pay",
    ],
)
def test_url_variants(raw: str) -> None:
    assert normalise(T.URL, raw) == "https://sbi-kyc.in/pay"


def test_url_root_and_junk() -> None:
    assert normalise(T.URL, "https://cybercrime.gov.in/") == "https://cybercrime.gov.in"
    for junk in ("test", "12345", "http://", "localhost", "http://192.168.1.1/x", "ftp://a.in", "a.b"):
        with pytest.raises(InvalidIdentifier):
            normalise(T.URL, junk)


@pytest.mark.parametrize("raw", ["VM-HDFCBK", "AD-HDFCBK", "HDFCBK", "hdfcbk", "VK-HDFCBK-T", "JD-HDFCBK-S"])
def test_sender_variants(raw: str) -> None:
    assert normalise(T.SENDER_ID, raw) == "HDFCBK"


def test_sender_junk() -> None:
    for junk in ("HDFC", "123456", "test", "VM-HDFC", "HDFCBANK"):
        with pytest.raises(InvalidIdentifier):
            normalise(T.SENDER_ID, junk)


def test_masks_match_brief() -> None:
    assert mask(T.PHONE, "+919876543210") == "98XXXXX210"
    assert mask(T.UPI, "ravi12@okaxis") == "r***@okaxis"
    assert mask(T.URL, "https://sbi-kyc.in/pay") == "sbi***.in/..."
    assert mask(T.SENDER_ID, "HDFCBK") == "HD****"


def test_all_19_verified_entries_normalise() -> None:
    assert len(VERIFIED) == 19
    assert (T.PHONE, "18001600") in VERIFIED
    assert (T.PHONE, "+918041002233") in VERIFIED
    assert (T.UPI, "freshbakes@okaxis") in VERIFIED
    assert (T.URL, "https://cybercrime.gov.in") in VERIFIED


def test_unknown_scam_type_becomes_other() -> None:
    assert canonical_scam_type("digital-arrest") == "digital-arrest"
    assert canonical_scam_type("crypto-rugpull") == "other"
    assert canonical_channel("phone call") == "Phone call"
    assert canonical_channel("carrier pigeon") == "Something else"
