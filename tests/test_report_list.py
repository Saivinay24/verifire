"""GET /lookup/reports: every report on one number, without who, what they wrote, or how much."""

from fastapi.testclient import TestClient

from tests.test_api_contract import _report

ROW_KEYS = {
    "occurred_at",
    "channel",
    "scam_type",
    "pincode",
    "locality",
    "city",
    "screenshot",
    "lost_money",
    "described",
}


def test_lists_every_report_with_proof_badges_and_nothing_private(client: TestClient) -> None:
    secret_note = "Ramesh Kumar from HSR, he took 45000 from my SBI account ending 4321"
    for n in range(1, 6):
        body = _report(n, value="98450 12121", amount_lost_inr=45000 if n == 1 else 0)
        if n == 1:
            body["note"] = secret_note
        assert client.post("/reports", json=body).status_code == 201
    r = client.get("/lookup/reports", params={"type": "phone", "value": "+91-98450-12121"})
    assert r.status_code == 200
    body = r.json()
    assert body["report_count"] == 5 and body["shown"] == 5 and len(body["reports"]) == 5
    assert all(set(x) == ROW_KEYS for x in body["reports"])
    times = [x["occurred_at"] for x in body["reports"]]
    assert times == sorted(times, reverse=True)  # newest first
    assert all(x["occurred_at"][14:19] == "00:00" for x in body["reports"])  # rounded to the hour
    assert all(x["locality"] == "HSR Layout" and x["city"] == "Bengaluru" for x in body["reports"])
    assert sum(x["lost_money"] for x in body["reports"]) == 1
    assert any(x["screenshot"] for x in body["reports"]) and any(not x["screenshot"] for x in body["reports"])
    raw = r.text
    for leak in (
        "Ramesh",
        "45000",
        "4321",
        '"r_1"',
        "103.1.58",
        "reporter_id",
        "reporter_key",
        "ip_key",
        "ip_prefix",
        "note",
        "amount",
    ):
        assert leak not in raw, leak


def test_same_answer_as_lookup_and_masked_under_three_people(client: TestClient) -> None:
    for n in (1, 2):
        client.post("/reports", json=_report(n, value="98450 34343"))
    look = client.get("/lookup", params={"type": "phone", "value": "9845034343"}).json()
    lst = client.get("/lookup/reports", params={"type": "phone", "value": "9845034343"}).json()
    assert lst["display_value"] == look["display_value"] and "34343" not in lst["display_value"]
    assert lst["verdict"] == look["verdict"] and lst["distinct_reporters"] == look["distinct_reporters"]


def test_verified_unreported_and_invalid(client: TestClient) -> None:
    for n in range(1, 4):
        client.post("/reports", json=_report(n, value="1930"))
    v = client.get("/lookup/reports", params={"type": "phone", "value": "1930"}).json()
    assert v["verdict"] == "VERIFIED_BUSINESS" and v["reports"] == []
    none = client.get("/lookup/reports", params={"type": "phone", "value": "9845099990"}).json()
    assert none["verdict"] == "NO_REPORTS" and none["reports"] == [] and none["shown"] == 0
    assert client.get("/lookup/reports", params={"type": "phone", "value": "1234"}).status_code == 400
