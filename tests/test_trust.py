"""Trust rules as pure functions: the verdict boundaries the README explains to judges."""

from dataclasses import replace
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
    reports = [facts(i, "" if i % 5 else "fraud number, beware everyone") for i in range(40)]
    assert "mostly_blank" in trust.evaluate(reports).pile_on
    assert verdict(reports) is trust.Verdict.SUSPICIOUS


def test_blank_victims_who_show_proof_are_not_a_blank_pile_on() -> None:
    # Blind eval G05: 8 victims, no words, every one attached a screenshot. Proof is saying something.
    reports = [facts(i, "", screenshot=True, lost=[0, 2000][i % 2]) for i in range(8)]
    result = trust.evaluate(reports)
    assert "mostly_blank" not in result.pile_on
    assert verdict(reports) is trust.Verdict.KNOWN_SCAM


def test_victims_may_pick_two_stages_of_one_script() -> None:
    # Blind eval G10: a customs-parcel call is the opening of a digital arrest; votes split 3 ways.
    types = ["digital-arrest", "courier-customs", "otp-call"]
    stories = [
        "FedEx parcel with drugs in my name, then a fake CBI officer on video call",
        "customs officer said my courier is seized and asked a fine by UPI",
        "otp call saying it was needed to release the parcel",
        "they kept me on skype for hours saying I am under digital arrest",
        "courier company call, then transferred to police, threatened arrest warrant",
        "asked me to read the otp to cancel the courier booking",
        "fake police station background, said aadhaar linked to money laundering",
        "parcel from Taiwan stopped at customs, pay processing fee or FIR",
    ]
    reports = [facts(i, stories[i], scam_type=types[i % 3]) for i in range(8)]
    assert "no_agreement_on_type" not in trust.evaluate(reports).pile_on
    assert verdict(reports) is trust.Verdict.KNOWN_SCAM


def _in_one_hour(n: int, note: str, **kw: object) -> trust.ReportFacts:
    r = facts(n, note, **kw)  # type: ignore[arg-type]
    t = datetime(2026, 10, 31, 12, tzinfo=UTC) + timedelta(minutes=n * 4)
    return replace(r, occurred_at=t, reported_at=t + timedelta(minutes=5))


def test_burst_of_stock_words_is_one_voice() -> None:
    # Blind eval A1_bomb10: 10 friends in one hour picking from four stock words, no proof.
    two = [_in_one_hour(i, ["scam", "fraud"][i % 2]) for i in range(10)]  # 2 distinct of 10: lockstep
    assert trust.evaluate(two).explain["merged_by"].get("lockstep_burst")
    assert verdict(two) is not trust.Verdict.KNOWN_SCAM
    words = ["scam", "fraud", "scam number", "cheater"]
    four = [_in_one_hour(i, words[i % 4]) for i in range(10)]  # 4 of 10: not lockstep, but no harm shown
    assert "no_harm_shown" in trust.evaluate(four).pile_on
    assert verdict(four) is not trust.Verdict.KNOWN_SCAM


def test_viral_wave_of_quiet_victims_with_losses_is_not_lockstep() -> None:
    # Blind eval G07: 12 victims in one hour, two thirds blank, but half of them lost money.
    reports = [
        _in_one_hour(i, "" if i % 3 else "otp scam", lost=[0, 15000][i % 2], screenshot=i == 4)
        for i in range(12)
    ]
    assert not trust.evaluate(reports).explain["merged_by"].get("lockstep_burst")
    assert verdict(reports) is trust.Verdict.KNOWN_SCAM


def test_many_people_no_harm_shown_never_confirms() -> None:
    # Blind eval A1_bomb40_slowdrip: 40 accounts over days, short varied words, nobody shows harm.
    words = ["scam number", "they cheated", "do not call this", "cheaters", "beware scam", "fraud"]
    reports = [facts(i, words[i % len(words)] + "!" * (i % 3)) for i in range(40)]
    result = trust.evaluate(reports)
    assert "no_harm_shown" in result.pile_on
    assert verdict(reports) is trust.Verdict.SUSPICIOUS
    assert not result.alert_ids


def test_no_harm_flood_cannot_bury_real_victims() -> None:
    # Self-poisoning with words: 4 real victims, then 50 "scam number" reports (harm share 7%).
    stories = [
        "pretended to be SBI, asked for the OTP, money gone",
        "said my KYC expired and sent a link, I lost 5000",
        "bank helpline caller wanted my card number and cvv",
        "told me to install anydesk to stop a refund, account emptied",
    ]
    victims = [facts(i, stories[i], lost=5000, screenshot=True) for i in range(4)]
    flood = [facts(10 + i, "scam number") for i in range(50)]
    assert "no_harm_shown" in trust._evaluate(victims + flood).pile_on
    assert verdict(victims) is trust.Verdict.KNOWN_SCAM
    assert verdict(victims + flood) is trust.Verdict.KNOWN_SCAM


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


def test_blank_flood_cannot_demote_an_established_scam() -> None:
    victims = [
        facts(1, "Caller pretending to be my bank asked for the OTP to stop a transaction"),
        facts(2, "bank se bol raha hoon bola, card block hoga, OTP maanga"),
        facts(3, "बैंक वाला बनकर कॉल किया और ओटीपी मांगा"),
        facts(4, "fake bank fraud team wanted my card number and the otp"),
    ]
    assert verdict(victims) is trust.Verdict.KNOWN_SCAM
    flood = [facts(10 + i, "", hours_ago=0.5) for i in range(15)]
    assert verdict(victims + flood) is trust.Verdict.KNOWN_SCAM
    # ...but a flood of blanks alone never confirms anything.
    assert verdict(flood) is trust.Verdict.SUSPICIOUS


def test_box_ticking_pile_on_with_no_words_never_confirms() -> None:
    # Catalog "30 blank reports all claiming proof": no words, every box ticked, types half agree.
    types = ["otp-call"] * 15 + ["other"] * 8 + ["lottery-prize"] * 7
    reports = [facts(i, "", scam_type=types[i], screenshot=True, lost=5000) for i in range(30)]
    result = trust.evaluate(reports)
    assert "mostly_blank" in result.pile_on and not result.explain["proof_counts"]
    assert verdict(reports) is trust.Verdict.SUSPICIOUS
