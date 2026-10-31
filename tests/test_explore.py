"""Explore: wording search and the confirmed-scams list.

The first test is the measurement quoted in app/services/explore.py and the README: 1,000 sends
of six scam scripts, each with a new number, name and amount and the edits forwards pick up.
"""

import random
from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.domain.notes import extract, similarity
from app.services.explore import SIMILAR_MIN
from judge.sms_scripts import SCRIPTS, fill
from judge.world import CLAIMS, Gen
from tests.test_api_contract import _report


def test_wording_search_separates_one_script_from_everything_else() -> None:
    r, g = random.Random(7), Gen(11, datetime.now(UTC))
    names = list(SCRIPTS)
    found = other = narrative = 0
    for _ in range(1000):
        a = r.choice(names)
        x = extract(fill(a, r)).signature
        found += similarity(x, extract(fill(a, r)).signature) >= SIMILAR_MIN
        b = r.choice([n for n in names if n != a])
        other += similarity(x, extract(fill(b, r)).signature) >= SIMILAR_MIN
        note = ""
        while len(note) < 25:
            note = g.victim_note(r.choice(list(CLAIMS)))
        narrative += similarity(x, extract(note).signature) >= SIMILAR_MIN
    assert found == 1000  # the same script from a new number is always found
    assert other == 0 and narrative == 0  # no false matches against other scripts or victim stories


def _campaign(client: TestClient, numbers: list[str], script: str, base: int) -> None:
    r = random.Random(base)
    for i, num in enumerate(numbers):
        for k in range(4):  # four people on four networks report each number
            n = base + i * 10 + k
            body = _report(n, value=num, ip_prefix=f"49.{n % 250}.{k}", reporter_id=f"v_{n}")
            client.post("/reports", json={**body, "message": fill(script, r, num=num)})


def test_a_script_that_moved_numbers_is_found_by_its_wording(client: TestClient) -> None:
    moved = ["9845011111", "9845022222", "9845033333"]
    _campaign(client, moved, "electricity", 100)
    _campaign(client, ["9845044444"], "lottery", 200)
    fresh = fill("electricity", random.Random(5), num="7000012345")  # a send nobody reported yet
    body = client.post("/explore/similar", json={"text": fresh}).json()
    shown = [m["display_value"] for m in body["matches"]]
    assert len(shown) == 3 and all(m["matching_reports"] == 4 for m in body["matches"])
    assert not any("44444" in v for v in shown)  # a different script is not a match
    m = body["matches"][0]
    assert set(m) == {
        "identifier_type", "display_value", "in_full", "verdict", "scam_type", "people",
        "last_seen", "matching_reports", "closeness", "cities",
    }  # fmt: skip
    assert m["verdict"] == "KNOWN_SCAM" and m["cities"] == ["Bengaluru"]


def test_a_pasted_message_does_not_look_like_a_brigade(client: TestClient) -> None:
    # Victims of a mass SMS paste the very same text. As notes that would read as one voice; as
    # the separate message field it must not change the verdict at all.
    text = fill("kyc", random.Random(3), num="9845055555")
    for k in range(4):
        n = 300 + k
        body = _report(n, value="9845055555", ip_prefix=f"49.{n % 250}.{k}", reporter_id=f"v_{n}")
        client.post("/reports", json={**body, "message": text})
    look = client.get("/lookup", params={"type": "phone", "value": "9845055555"}).json()
    assert look["verdict"] == "KNOWN_SCAM"


def test_wording_search_needs_a_sentence_and_finds_nothing_unrelated(client: TestClient) -> None:
    _campaign(client, ["9845066666"], "parcel", 400)
    assert client.post("/explore/similar", json={"text": "hi"}).status_code == 400
    assert client.post("/explore/similar", json={}).status_code == 400
    body = client.post(
        "/explore/similar", json={"text": "Lunch at 1 tomorrow near the office, see you there"}
    )
    assert body.json()["matches"] == []


def test_known_list_shows_only_confirmed_scams_and_filters(client: TestClient) -> None:
    _campaign(client, ["9845077777"], "arrest", 500)
    client.post("/reports", json=_report(600, value="9845088888"))  # one report: not confirmed
    body = client.get("/explore/known").json()
    values = [s["display_value"] for s in body["scams"]]
    assert any("77777" in v for v in values) and not any("88888" in v for v in values)
    assert client.get("/explore/known", params={"city": "Mumbai"}).json()["scams"] == []
    assert client.get("/explore/known", params={"scam_type": "digital-arrest"}).json()["total"] == 1
