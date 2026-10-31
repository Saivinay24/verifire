"""Appendix A contracts: shapes, status codes, defaults. Runs against the real database."""

from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi.testclient import TestClient

from harness.run import run_suite

LOOKUP_KEYS = {
    "verdict",
    "report_count",
    "distinct_reporters",
    "first_seen",
    "last_seen",
    "scam_type",
    "display_value",
    "evidence",
    "challenged",
}


# Different people describing one scam in their own words (copy-pasted notes would be merged).
NOTES = [
    "Video call from a man in police uniform, said a parcel with drugs was in my name",
    "Mujhe CBI officer bolke call aaya, arrest ka darr dikhaya aur paise maange",
    "They kept me on skype for three hours and asked me to transfer money to clear my name",
    "पुलिस वाला बनकर वीडियो कॉल किया और गिरफ्तारी की धमकी दी",
    "Caller said customs seized my courier and I must pay a fine immediately",
    "My father got the call, they showed a fake FIR copy and demanded 2 lakh",
    "Fake officer on WhatsApp video asked for my Aadhaar and bank details",
]


def _report(n: int, value: str = "+91 98765 43210", **over: Any) -> dict[str, Any]:
    t = datetime.now(UTC) - timedelta(hours=2, minutes=n)
    body = {
        "report_id": f"rep_{n}",
        "occurred_at": t.isoformat(timespec="seconds"),
        "reported_at": (t + timedelta(minutes=10)).isoformat(timespec="seconds"),
        "reporter_id": f"r_{n}",
        "ip_prefix": f"103.{n}.58",
        "channel": "Phone call",
        "scam_type": "digital-arrest",
        "identifier_type": "phone",
        "identifier_value": value,
        "pincode": "560102",
        "locality": "HSR Layout",
        "city": "Bengaluru",
        "note": NOTES[(n + n // 7) % len(NOTES)],
        "has_screenshot": n % 2 == 0,
        "amount_lost_inr": 0,
    }
    body.update(over)
    return body


def test_post_report_201_shape_and_merged(client: TestClient) -> None:
    first = client.post("/reports", json=_report(1))
    assert first.status_code == 201
    assert first.json() == {"report_id": "rep_1", "case_id": first.json()["case_id"], "merged": False}
    second = client.post("/reports", json=_report(2, value="09876543210"))
    assert second.status_code == 201
    assert second.json()["merged"] is True
    assert second.json()["case_id"] == first.json()["case_id"]


def test_duplicate_report_id_is_idempotent(client: TestClient) -> None:
    client.post("/reports", json=_report(1))
    again = client.post("/reports", json=_report(1))
    assert again.status_code == 201
    body = client.get("/lookup", params={"type": "phone", "value": "+919876543210"}).json()
    assert body["report_count"] == 1


def test_invalid_reports_are_400(client: TestClient) -> None:
    for over in (
        {"identifier_value": "12345"},
        {"identifier_value": "test"},
        {"identifier_value": ""},
        {"pincode": "999999"},
        {"occurred_at": "yesterday"},
        {"occurred_at": "2026-10-27T18:21:04"},  # no offset
        {"identifier_type": "email"},
    ):
        r = client.post("/reports", json=_report(5, **over))
        assert r.status_code == 400, over
        assert "error" in r.json()
    assert (
        client.post("/reports", content=b"not json", headers={"content-type": "application/json"}).status_code
        == 400
    )


def test_unknown_scam_type_is_accepted_as_other(client: TestClient) -> None:
    assert client.post("/reports", json=_report(1, scam_type="crypto-rugpull")).status_code == 201
    body = client.get("/lookup", params={"type": "phone", "value": "9876543210"}).json()
    assert body["scam_type"] == "other"


def test_lookup_contract_masking_and_privacy(client: TestClient) -> None:
    client.post("/reports", json=_report(1))
    body = client.get("/lookup", params={"type": "phone", "value": "+91 98765 43210"}).json()
    assert body.keys() >= LOOKUP_KEYS
    assert body["verdict"] == "SUSPICIOUS"
    assert body["display_value"] == "98XXXXX210"
    assert body["evidence"] and set(body["evidence"][0]) == {"occurred_at", "channel", "scam_type", "pincode"}
    raw = client.get("/lookup", params={"type": "phone", "value": "+91 98765 43210"}).text
    for secret in ("r_1", "103.1.58", "police uniform"):
        assert secret not in raw


def test_three_independent_people_make_known_scam_and_unmask(client: TestClient) -> None:
    variants = ["+91 98765 43210", "09876543210", "98765-43210", "919876543210"]
    for n, v in enumerate(variants, start=1):
        assert client.post("/reports", json=_report(n * 7, value=v)).status_code == 201
    for v in variants:
        body = client.get("/lookup", params={"type": "phone", "value": v}).json()
        assert body["verdict"] == "KNOWN_SCAM"
        assert body["distinct_reporters"] == 4
        assert body["display_value"] == "+919876543210"
        assert body["summary"] == "Reported by 4 people near you"


def test_unreported_is_200_no_reports_and_junk_is_400(client: TestClient) -> None:
    r = client.get("/lookup", params={"type": "phone", "value": "+91 91234 56789"})
    assert r.status_code == 200
    assert r.json()["verdict"] == "NO_REPORTS"
    assert client.get("/lookup", params={"type": "phone", "value": "12345"}).status_code == 400
    assert client.get("/lookup", params={"type": "nope", "value": "x"}).status_code == 400


def test_verified_entries_stay_verified_under_reports(client: TestClient) -> None:
    for n in range(1, 8):
        client.post("/reports", json=_report(n * 3, value="1930"))
    for t, v in (
        ("phone", "1930"),
        ("phone", "1800 1600"),
        ("sender_id", "AD-HDFCBK"),
        ("upi", "FreshBakes@OKAXIS"),
    ):
        body = client.get("/lookup", params={"type": t, "value": v}).json()
        assert body["verdict"] == "VERIFIED_BUSINESS", v


def test_challenge_caps_at_suspicious(client: TestClient) -> None:
    for n in range(1, 6):
        client.post("/reports", json=_report(n * 7))
    assert (
        client.get("/lookup", params={"type": "phone", "value": "9876543210"}).json()["verdict"]
        == "KNOWN_SCAM"
    )
    r = client.post(
        "/challenges",
        json={
            "identifier_type": "phone",
            "identifier_value": "+91 98765 43210",
            "claimant_name": "Fresh Bakes",
            "contact_email": "owner@example.com",
            "proof_note": "GST certificate attached.",
        },
    )
    assert r.status_code == 201
    assert r.json()["status"] == "under_review"
    body = client.get("/lookup", params={"type": "phone", "value": "9876543210"}).json()
    assert body["challenged"] is True
    assert body["verdict"] == "SUSPICIOUS"
    client.post("/reports", json=_report(99))
    assert (
        client.get("/lookup", params={"type": "phone", "value": "9876543210"}).json()["verdict"]
        == "SUSPICIOUS"
    )
    assert (
        "owner@example.com" not in client.get("/lookup", params={"type": "phone", "value": "9876543210"}).text
    )


def test_map_defaults_window_and_centroids(client: TestClient) -> None:
    client.post("/reports", json=_report(1))
    old = datetime.now(UTC) - timedelta(days=30)
    client.post(
        "/reports",
        json=_report(2, value="+91 91111 22222", occurred_at=old.isoformat(), reported_at=old.isoformat()),
    )
    body = client.get("/map", params={"pincode": "560102"}).json()
    assert body["clusters"] == [
        {
            "pincode": "560102",
            "locality": "HSR Layout",
            "city": "Bengaluru",
            "count": 1,
            "top_scam_type": "digital-arrest",
            "severity": "MED",
            "lat": 12.9116,
            "lng": 77.6473,
        }
    ]
    assert client.get("/map", params={"pincode": "000000"}).status_code == 400


def test_alerts_spike_new_type_and_quiet(client: TestClient) -> None:
    assert client.get("/alerts", params={"pincode": "560034"}).json() == {"alerts": []}
    for n in range(1, 7):
        client.post("/reports", json=_report(n, value=f"+91 9{n}876 5432{n}", scam_type="job-offer"))
    alerts = client.get("/alerts", params={"pincode": "560102"}).json()["alerts"]
    kinds = {a["type"] for a in alerts}
    assert kinds == {"SPIKE", "NEW_TYPE"}
    spike = next(a for a in alerts if a["type"] == "SPIKE")
    assert spike["count"] == 6 and spike["window"] == "24h" and spike["baseline_per_day"] == 0
    assert client.get("/alerts", params={"pincode": "560038"}).json() == {"alerts": []}


def test_sybils_spread_over_many_numbers_never_alert(client: TestClient) -> None:
    for n in range(1, 21):
        client.post(
            "/reports", json=_report(n, value=f"+91 9{n % 10}{n:02d}7 6543{n % 10}", ip_prefix="49.36.12")
        )
    assert client.get("/alerts", params={"pincode": "560102"}).json()["alerts"] == [] or all(
        a["type"] != "SPIKE" for a in client.get("/alerts", params={"pincode": "560102"}).json()["alerts"]
    )


def test_reset_deletes_reports(client: TestClient) -> None:
    client.post("/reports", json=_report(1))
    r = client.post("/admin/reset")
    assert r.status_code == 200
    assert (
        client.get("/lookup", params={"type": "phone", "value": "9876543210"}).json()["verdict"]
        == "NO_REPORTS"
    )


def test_trust_harness_two_seeds(client: TestClient) -> None:
    log: list[str] = []
    result = run_suite(client, [7, 8], log)
    assert result["failures"] == [], "\n".join(log)


def test_lookup_cache_never_serves_a_stale_answer(client: TestClient) -> None:
    value = "+91 70000 12345"
    assert client.get("/lookup", params={"type": "phone", "value": value}).json()["report_count"] == 0
    assert client.post("/reports", json=_report(900, value=value)).status_code == 201
    assert client.get("/lookup", params={"type": "phone", "value": value}).json()["report_count"] == 1
    client.post("/admin/reset")
    assert client.get("/lookup", params={"type": "phone", "value": value}).json()["report_count"] == 0
