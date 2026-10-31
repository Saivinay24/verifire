"""City sheet and live statistics: trends are built only from reports the trust engine counted."""

from fastapi.testclient import TestClient

from tests.test_api_contract import _report

REAL = "+91 98765 43210"
FARM = "+91 91234 56789"
TWO = "+91 99887 76655"
FEED_KEYS = {
    "occurred_at",
    "channel",
    "scam_type",
    "pincode",
    "locality",
    "identifier_type",
    "display_value",
    "verdict",
}


def _load(client: TestClient) -> None:
    for n in range(1, 6):  # five real people, different connections and words
        assert client.post("/reports", json=_report(n, REAL)).status_code == 201
    for n in range(22):  # 22 accounts on one connection, one person
        body = _report(100 + n, FARM, ip_prefix="49.36.12", scam_type="lottery-prize", note="")
        assert client.post("/reports", json=body).status_code == 201
    for n in (201, 202):  # two people: stays masked
        assert client.post("/reports", json=_report(n, TWO, scam_type="otp-call")).status_code == 201


def test_city_counts_people_and_masks_under_three(client: TestClient) -> None:
    _load(client)
    body = client.get("/city", params={"pincode": "560034"}).json()  # Koramangala, same city as HSR
    assert body["city"] == "Bengaluru"
    assert body["reports"] == 29
    assert body["counted"] == 5 + 2  # the farm is one group of 22 reports: spam, never a trend
    assert [k["display_value"] for k in body["known_scams"]] == ["+919876543210"]
    assert body["known_scams"][0]["people"] == 5
    shown = {f["display_value"] for f in body["recent"]}
    assert "+919876543210" in shown
    assert "99XXXXX655" in shown and "+919988776655" not in str(body)
    assert "+919123456789" not in str(body)
    assert body["scam_types"][0] == {"scam_type": "digital-arrest", "count": 5, "share": 0.714}
    hsr = next(a for a in body["areas"] if a.get("pincode") == "560102")
    assert hsr["locality"] == "HSR Layout" and hsr["lat"] == 12.9116


def test_city_feed_has_no_reporter_data_and_hour_times(client: TestClient) -> None:
    _load(client)
    body = client.get("/city", params={"pincode": "560102"}).json()
    for item in body["recent"]:
        assert set(item) == FEED_KEYS
        assert item["occurred_at"][14:19] == "00:00"
    text = str(body)
    for secret in ("r_1", "103.1.58", "49.36.12", "Video call from a man"):
        assert secret not in text


def test_city_rejects_unknown_area_and_bad_days(client: TestClient) -> None:
    assert client.get("/city", params={"pincode": "999999"}).status_code == 400
    assert client.get("/city", params={"pincode": "560102", "days": "0"}).status_code == 400
    assert client.get("/city", params={"pincode": "560102", "days": "abc"}).status_code == 400
    empty = client.get("/city", params={"pincode": "400050"}).json()
    assert empty["city"] == "Mumbai" and empty["reports"] == 0 and empty["recent"] == []


def test_stats_set_aside_and_breakdowns_add_up(client: TestClient) -> None:
    _load(client)
    body = client.get("/stats").json()
    assert body["reports"] == 29 and body["counted"] == 7 and body["set_aside"] == 22
    assert body["numbers_reported"] == 3 and body["known_scam_numbers"] == 1
    for key in ("by_scam_type", "by_channel", "by_city"):
        assert sum(x["count"] for x in body[key]) == body["counted"]
    assert body["by_city"] == [{"city": "Bengaluru", "count": 7, "share": 1.0}]
    assert len(body["daily"]) == 14
    assert sum(d["reports"] for d in body["daily"]) == 29
    assert body["this_week"] == 7 and body["last_week"] == 0
    assert client.get("/stats", params={"days": "-1"}).status_code == 400
