"""Dispute lifecycle: a dispute protects a wrongly reported owner but can't shield a scammer.

Each test is one real-life case. Server receive times can't be set by a client, so tests move
rows into the past directly, as if hours or days had gone by.
"""

from collections.abc import Iterator
from typing import Any

import pytest
import sqlalchemy as sa
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import get_engine
from app.services import challenges, lookup
from tests.test_api_contract import _report

NUMBER = "+91 98765 43210"
KEY = "test-review-key"
OWNER = {
    "identifier_type": "phone",
    "identifier_value": NUMBER,
    "claimant_name": "Fresh Bakes",
    "contact_email": "owner@example.com",
    "proof_note": "GST certificate attached.",
}


@pytest.fixture
def reviewer() -> Iterator[None]:
    settings = get_settings()
    old = settings.review_key
    settings.review_key = KEY
    yield
    settings.review_key = old


def _look(client: TestClient, value: str = NUMBER) -> dict[str, Any]:
    return client.get("/lookup", params={"type": "phone", "value": value}).json()  # type: ignore[no-any-return]


def _known(client: TestClient) -> None:
    for n in range(1, 6):
        assert client.post("/reports", json=_report(n * 7)).status_code == 201
    assert _look(client)["verdict"] == "KNOWN_SCAM"


def _sql(stmt: str, **params: Any) -> None:
    with get_engine().begin() as conn:
        conn.execute(sa.text(stmt), params)
    lookup.invalidate()


def _new_victims(client: TestClient, ns: range, spread_hours: list[int] | None = None) -> None:
    """New people on new networks report after the dispute; optionally spread over hours."""
    for n in ns:
        assert (
            client.post(
                "/reports", json=_report(n, ip_prefix=f"49.{n}.12", reporter_id=f"new_{n}")
            ).status_code
            == 201
        )
    if spread_hours:
        # Pretend the dispute opened two days ago and these reports arrived hours apart since.
        _sql("UPDATE challenges SET created_at = now() - interval '2 days'")
        for n, h in zip(ns, spread_hours, strict=True):
            _sql(
                "UPDATE reports SET received_at = (SELECT created_at FROM challenges LIMIT 1)"
                " + make_interval(hours => :h) WHERE report_id = :rid",
                h=h,
                rid=f"rep_{n}",
            )


def test_dispute_caps_at_suspicious_and_keeps_the_evidence(client: TestClient) -> None:
    _known(client)
    assert client.post("/challenges", json=OWNER).status_code == 201
    body = _look(client)
    assert body["verdict"] == "SUSPICIOUS" and body["challenged"] is True
    # People are still warned: the counts and scam type stay, and the deadline is public.
    assert body["distinct_reporters"] >= 3 and body["scam_type"] == "digital-arrest"
    assert body["dispute"]["status"] == "under_review" and body["dispute"]["closes_at"]
    assert "owner@example.com" not in str(body) and "Fresh Bakes" not in str(body)


def test_a_burst_right_after_the_dispute_does_not_break_it(client: TestClient) -> None:
    # The harassment pattern: a business disputes, and the same crowd fires reports at once.
    _known(client)
    client.post("/challenges", json=OWNER)
    _new_victims(client, range(60, 66))
    body = _look(client)
    assert body["verdict"] == "SUSPICIOUS" and body["challenged"] is True


def test_new_victims_over_hours_overrule_the_dispute(client: TestClient) -> None:
    # A scammer disputes, keeps scamming, and new people report it through the day.
    _known(client)
    client.post("/challenges", json=OWNER)
    _new_victims(client, range(60, 64), spread_hours=[1, 4, 9, 20])
    client.post(
        "/reports", json=_report(64, ip_prefix="49.64.12", reporter_id="new_64")
    )  # any new report re-checks
    body = _look(client)
    assert body["verdict"] == "KNOWN_SCAM" and body["challenged"] is False
    assert body["dispute"]["status"] == "overruled"
    # ...and the same number can't be disputed again for a while.
    again = client.post("/challenges", json={**OWNER, "contact_email": "other@example.com"})
    assert again.status_code == 409 and again.json()["status"] == "overruled"


FRESH = [
    "Same man called again from this number and said my arrest warrant was ready",
    "He phoned my wife this time and asked for 50,000 to close the case",
    "Another video call today, he showed a fake court order and shouted",
    "Called once more at night asking for my bank OTP to verify the case",
    "This time he said my Aadhaar was linked to money laundering",
]


def test_the_original_accusers_cannot_overrule(client: TestClient) -> None:
    # The people who reported before the dispute report again, in new words, over hours. Without
    # the "new people only" rule this would overrule (see the mutation note in the commit).
    _known(client)
    client.post("/challenges", json=OWNER)
    _sql("UPDATE challenges SET created_at = now() - interval '2 days'")
    _sql("UPDATE reports SET received_at = now() - interval '3 days'")  # before the dispute
    for i, n in enumerate((7, 14, 21, 28, 35)):
        rid = f"again_{n}"
        body = {**_report(n), "report_id": rid, "note": FRESH[i], "has_screenshot": True}
        assert client.post("/reports", json=body).status_code == 201
        _sql(
            "UPDATE reports SET received_at = now() - make_interval(hours => :h) WHERE report_id = :rid",
            h=20 - i * 5,
            rid=rid,
        )
    client.post(
        "/reports", json={**_report(42), "report_id": "again_42", "note": "Again today, same threats"}
    )
    assert _look(client)["challenged"] is True


def test_a_pre_emptive_dispute_is_no_shield(client: TestClient) -> None:
    # A scammer disputes a fresh number before anyone reports it.
    assert client.post("/challenges", json=OWNER).status_code == 201
    assert _look(client)["verdict"] == "NO_REPORTS"
    _new_victims(client, range(60, 64), spread_hours=[1, 4, 9, 20])
    client.post("/reports", json=_report(64, ip_prefix="49.64.12", reporter_id="new_64"))
    assert _look(client)["verdict"] == "KNOWN_SCAM"


def test_an_undecided_dispute_lapses_at_its_deadline(client: TestClient) -> None:
    _known(client)
    client.post("/challenges", json=OWNER)
    _sql("UPDATE challenges SET closes_at = now() - interval '1 minute'")
    assert challenges.sweep(force=True) == 1
    lookup.invalidate()
    body = _look(client)
    assert body["verdict"] == "KNOWN_SCAM" and body["dispute"]["status"] == "lapsed"
    assert client.post("/challenges", json=OWNER).status_code == 409


def test_reviewing_is_off_without_a_key(client: TestClient) -> None:
    assert client.get("/review/disputes").status_code == 404


def test_reviewer_upholds_a_wrongly_reported_owner(client: TestClient, reviewer: None) -> None:
    _known(client)
    client.post("/challenges", json=OWNER)
    assert client.get("/review/disputes").status_code == 401
    queue = client.get("/review/disputes", headers={"x-review-key": KEY}).json()["disputes"]
    item = queue[0]
    assert item["claimant_name"] == "Fresh Bakes" and item["evidence"]["people"] >= 3
    assert item["same_contact_disputes"] == 1
    r = client.post(
        f"/review/disputes/{item['challenge_id']}", json={"decision": "upheld"}, headers={"x-review-key": KEY}
    )
    assert r.status_code == 200
    body = _look(client)
    assert body["verdict"] == "NO_REPORTS" and body["report_count"] == 0 and body["evidence"] == []
    # The number starts fresh: a new real report counts as usual.
    client.post("/reports", json=_report(80, ip_prefix="49.80.12", reporter_id="new_80"))
    assert _look(client)["report_count"] == 1


def test_reviewer_rejects_a_scammer_and_the_number_is_locked(client: TestClient, reviewer: None) -> None:
    _known(client)
    cid = client.post("/challenges", json=OWNER).json()["challenge_id"]
    client.post(f"/review/disputes/{cid}", json={"decision": "rejected"}, headers={"x-review-key": KEY})
    body = _look(client)
    assert body["verdict"] == "KNOWN_SCAM" and body["dispute"]["status"] == "rejected"
    assert client.post("/challenges", json=OWNER).status_code == 409


def test_bulk_disputes_are_visible_to_the_reviewer_and_capped(client: TestClient, reviewer: None) -> None:
    # One contact disputing many numbers is the scammer pattern; the reviewer sees the count.
    for i in range(20):
        body = {**OWNER, "identifier_value": f"98450{i:05d}"}
        assert client.post("/challenges", json=body).status_code == 201
    assert client.post("/challenges", json={**OWNER, "identifier_value": "9845099999"}).status_code == 429
    queue = client.get("/review/disputes", headers={"x-review-key": KEY}).json()["disputes"]
    assert {d["same_contact_disputes"] for d in queue} == {20}
    assert {d["same_network_disputes"] for d in queue} == {20}
