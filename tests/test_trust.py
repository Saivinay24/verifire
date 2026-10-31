"""Trust rules as pure functions: the verdict boundaries the README explains to judges."""

from datetime import UTC, datetime, timedelta

from app.domain import trust
from app.domain.notes import extract


def facts(
    n: int,
    note: str,
    *,
    scam_type: str = "otp-call",
    ip: str | None = None,
    reporter: str | None = None,
    screenshot: bool = False,
    lost: int = 0,
    hours_ago: float = 0,
) -> trust.ReportFacts:
    f = extract(note)
    t = datetime(2026, 10, 31, 12, tzinfo=UTC) - timedelta(hours=hours_ago or n * 3)
    return trust.ReportFacts(
        id=f"r{n}",
        reporter_key=reporter or f"person{n}",
        ip_key=ip or f"net{n}",
        occurred_at=t,
        reported_at=t + timedelta(hours=2),
        pincode="560102",
        scam_type=scam_type,
        note_len=f.length,
        note_sig=f.signature,
        note_lex=f.mentions_method,
        note_scam=f.names_scam,
        note_review=f.is_review,
        has_screenshot=screenshot,
        amount_lost_inr=lost,
    )


def verdict(reports: list[trust.ReportFacts]) -> trust.Verdict:
    return trust.decide(
        verified=False, challenged=False, report_count=len(reports), result=trust.evaluate(reports)
    )


def test_three_people_two_describing_is_known() -> None:
    reports = [
        facts(1, "Caller pretending to be my bank asked for the OTP to stop a transaction", lost=2000),
        facts(2, "", lost=98000),
        facts(3, ""),
    ]
    assert verdict(reports) is trust.Verdict.KNOWN_SCAM


def test_three_blank_clicks_are_not_enough() -> None:
    assert verdict([facts(i, "") for i in range(3)]) is trust.Verdict.SUSPICIOUS


def test_friends_writing_shop_reviews_never_confirm() -> None:
    reviews = [
        "stale bread at this shop",
        "rude owner, never go",
        "overpriced cakes",
        "dirty kitchen, 1 star",
        "expired cream in the pastry",
        "staff misbehaved with us",
        "worst bakery around",
        "bad quality food",
    ]
    reports = [facts(i, reviews[i % len(reviews)] + f" {i}", screenshot=True, lost=500) for i in range(40)]
    result = trust.evaluate(reports)
    assert "reviews_not_scams" in result.pile_on
    assert verdict(reports) is trust.Verdict.SUSPICIOUS
    assert not result.alert_ids  # and they never set off an alert


def test_mostly_blank_pile_on_never_confirms() -> None:
    reports = [facts(i, "" if i % 5 else "fraud number, beware everyone", lost=1000) for i in range(40)]
    assert "mostly_blank" in trust.evaluate(reports).pile_on
    assert verdict(reports) is trust.Verdict.SUSPICIOUS


def test_reporters_who_cannot_agree_on_the_scam_never_confirm() -> None:
    types = ["otp-call", "lottery-prize", "job-offer", "sextortion"]
    reports = [
        facts(i, f"they asked for OTP and money transfer number {i}", scam_type=types[i % 4])
        for i in range(12)
    ]
    assert "no_agreement_on_type" in trust.evaluate(reports).pile_on


def test_one_person_many_times_is_one_and_never_alerts() -> None:
    reports = [facts(i, "asked for OTP pretending to be from bank", reporter="same") for i in range(6)]
    result = trust.evaluate(reports)
    assert result.groups == 1
    assert not result.alert_ids


def test_real_campaign_with_plain_notes_is_known_and_alerts() -> None:
    notes = ["fraud call, asked otp", "scam call aaya bank ke naam pe", "बैंक वाला बनकर ओटीपी मांगा",
             "fake bank guy wanted card details", "asked OTP for KYC", "otp maanga card block bol ke",
             "bank fraud team they said, wanted the otp", "fake call from bank"]  # fmt: skip
    reports = [facts(i, n) for i, n in enumerate(notes)]
    result = trust.evaluate(reports)
    assert not result.pile_on
    assert verdict(reports) is trust.Verdict.KNOWN_SCAM
    assert len(result.alert_ids) == len(notes)
